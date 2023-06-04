import os
import re
import html
import logging

from azure.ai.formrecognizer import DocumentAnalysisClient, AnalyzeResult
from azure.search.documents import SearchClient

logger = logging.getLogger("indexer")

MAX_SECTION_LENGTH = 1000
SENTENCE_SEARCH_LIMIT = 100
SECTION_OVERLAP = 100


class CognitiveIndex:
    def __init__(
        self,
        filename: str,
        file_data: bytes,
        formrecognizer: DocumentAnalysisClient,
        cognitive_search: SearchClient,
        category: str | None,
    ) -> None:
        logger.info("Analyzing document...")
        lro_poller = formrecognizer.begin_analyze_document(
            model_id="prebuilt-layout", document=file_data
        )
        results = lro_poller.result()
        logger.info("Creating page map and sections...")
        page_map = self.get_page_map(form_result=results)
        sections = self.create_sections(
            filename=filename, page_map=page_map, category=category
        )
        logger.info("Indexing Sections...")
        self.index_sections(client=cognitive_search, sections=sections)

    def get_page_map(self, form_result: AnalyzeResult) -> list[tuple[str]]:
        offset = 0
        page_map = []
        for page_num, page in enumerate(form_result.pages):
            tables_on_page = [
                table
                for table in form_result.tables
                if table.bounding_regions[0].page_number == page_num + 1
            ]

            page_offset = page.spans[0].offset
            page_length = page.spans[0].length
            table_chars = [-1] * page_length
            for table_id, table in enumerate(tables_on_page):
                for span in table.spans:
                    for i in range(span.length):
                        idx = span.offset - page_offset + i
                        if idx >= 0 and idx < page_length:
                            table_chars[idx] = table_id

            page_text = ""
            added_tables = set()
            for idx, table_id in enumerate(table_chars):
                if table_id == -1:
                    page_text += form_result.content[page_offset + idx]
                elif not table_id in added_tables:
                    page_text += self.table_to_html(tables_on_page[table_id])
                    added_tables.add(table_id)

            page_text += " "
            page_map.append((page_num, offset, page_text))
            offset += len(page_text)

        return page_map

    def table_to_html(self, table) -> html:
        table_html = "<table>"
        rows = [
            sorted(
                [cell for cell in table.cells if cell.row_index == i],
                key=lambda cell: cell.column_index,
            )
            for i in range(table.row_count)
        ]
        for row_cells in rows:
            table_html += "<tr>"
            for cell in row_cells:
                tag = (
                    "th"
                    if (cell.kind == "columnHeader" or cell.kind == "rowHeader")
                    else "td"
                )
                cell_spans = ""
                if cell.column_span > 1:
                    cell_spans += f" colSpan={cell.column_span}"
                if cell.row_span > 1:
                    cell_spans += f" rowSpan={cell.row_span}"
                table_html += f"<{tag}{cell_spans}>{html.escape(cell.content)}</{tag}>"
            table_html += "</tr>"
        table_html += "</table>"
        return table_html

    def create_sections(
        self, filename: str, page_map: list[tuple[str]], category: str | None
    ) -> dict:
        for i, (section, pagenum) in enumerate(self.split_text(page_map)):
            yield {
                "id": re.sub("[^0-9a-zA-Z_-]", "_", f"{filename}-{i}"),
                "content": section,
                "category": category,
                "sourcepage": self.blob_name_from_file_page(filename, pagenum),
                "sourcefile": filename,
            }

    def blob_name_from_file_page(self, filename: str, page=0) -> str:
        if os.path.splitext(filename)[1].lower() == ".pdf":
            return os.path.splitext(os.path.basename(filename))[0] + f"-{page}" + ".pdf"
        else:
            return os.path.basename(filename)

    def split_text(self, page_map: str) -> tuple:
        SENTENCE_ENDINGS = [".", "!", "?"]
        WORDS_BREAKS = [",", ";", ":", " ", "(", ")", "[", "]", "{", "}", "\t", "\n"]

        def find_page(offset):
            l = len(page_map)
            for i in range(l - 1):
                if offset >= page_map[i][1] and offset < page_map[i + 1][1]:
                    return i
            return l - 1

        all_text = "".join(p[2] for p in page_map)
        length = len(all_text)
        start = 0
        end = length
        while start + SECTION_OVERLAP < length:
            last_word = -1
            end = start + MAX_SECTION_LENGTH

            if end > length:
                end = length
            else:
                while (
                    end < length
                    and (end - start - MAX_SECTION_LENGTH) < SENTENCE_SEARCH_LIMIT
                    and all_text[end] not in SENTENCE_ENDINGS
                ):
                    if all_text[end] in WORDS_BREAKS:
                        last_word = end
                    end += 1
                if (
                    end < length
                    and all_text[end] not in SENTENCE_ENDINGS
                    and last_word > 0
                ):
                    end = last_word
            if end < length:
                end += 1

            last_word = -1
            while (
                start > 0
                and start > end - MAX_SECTION_LENGTH - 2 * SENTENCE_SEARCH_LIMIT
                and all_text[start] not in SENTENCE_ENDINGS
            ):
                if all_text[start] in WORDS_BREAKS:
                    last_word = start
                start -= 1
            if all_text[start] not in SENTENCE_ENDINGS and last_word > 0:
                start = last_word
            if start > 0:
                start += 1

            section_text = all_text[start:end]
            yield (section_text, find_page(start))

            last_table_start = section_text.rfind("<table")
            if (
                last_table_start > 2 * SENTENCE_SEARCH_LIMIT
                and last_table_start > section_text.rfind("</table")
            ):
                start = min(end - SECTION_OVERLAP, start + last_table_start)
            else:
                start = end - SECTION_OVERLAP

        if start + SECTION_OVERLAP < end:
            yield (all_text[start:end], find_page(start))

    def index_sections(self, client: SearchClient, sections: dict):
        i = 0
        batch = []
        for s in sections:
            batch.append(s)
            i += 1
            if i % 1000 == 0:
                results = client.upload_documents(documents=batch)
                succeeded = sum([1 for r in results if r.succeeded])
                batch = []

        if len(batch) > 0:
            results = client.upload_documents(documents=batch)
            succeeded = sum([1 for r in results if r.succeeded])
