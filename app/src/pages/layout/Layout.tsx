import { useState } from "react";
import { Outlet, Link } from "react-router-dom";
import { Grid } from "react-loader-spinner";
import styles from "./Layout.module.css";
import { uploadApi } from "../../api";
import { UploadRequest } from "../../api";

const Layout = () => {
    const [isLoading, setIsLoading] = useState(false);
    const [category, setCategory] = useState("");
    const [fileName, setFileName] = useState("");
    const handleFileChange = e => {
        const file = e.target.files[0];
        setFileName(file.name);
    };
    const handleFileUpload = async () => {
        const fileInput = document.getElementById("fileInput") as HTMLInputElement;
        const inputFile = fileInput.files[0];

        setIsLoading(true);
        let upload: UploadRequest;
        if (category != null) {
            upload = {
                file: inputFile
            };
        } else {
            upload = {
                file: inputFile,
                category: category
            };
        }

        try {
            const response = await uploadApi(upload);
            console.log(response);
        } catch (error) {
            console.error(error);
        }

        setIsLoading(false);
    };
    const handleCategoryChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        setCategory(event.target.value);
    };

    return (
        <div className={styles.layout}>
            <header className={styles.header} role={"banner"}>
                <div className={styles.headerContainer}>
                    <Link to="/" className={styles.headerTitleContainer}>
                        <h3 className={styles.headerTitle}>Athena | Amagi AI</h3>
                    </Link>
                    <nav>
                        <ul className={styles.headerNavList}>
                            <li className={styles.headerNavLeftMargin}>
                                <h3>Upload you pdf here -</h3>
                            </li>
                            <li className={styles.headerNavLeftMargin}>
                                <input className={styles.fileInput} type="file" id="fileInput" onChange={handleFileChange} />
                                <label htmlFor="fileInput" className={styles.fileInputLabel}>
                                    {fileName ? fileName : "Choose File"}
                                </label>
                            </li>
                            <li>
                                <input
                                    className={styles.category}
                                    type="text"
                                    placeholder="(Optional) Category"
                                    value={category}
                                    onChange={handleCategoryChange}
                                />
                            </li>
                            <li>
                                {isLoading ? (
                                    <div className={styles.spinner}>
                                        <Grid
                                            height="30"
                                            width="30"
                                            color="#DD6D51"
                                            ariaLabel="grid-loading"
                                            radius="12.5"
                                            wrapperStyle={{}}
                                            wrapperClass=""
                                            visible={true}
                                        />
                                    </div>
                                ) : (
                                    <button disabled={isLoading} onClick={handleFileUpload} className={styles.fileInputLabel}>
                                        Upload
                                    </button>
                                )}
                            </li>
                        </ul>
                    </nav>
                </div>
            </header>

            <Outlet />
        </div>
    );
};

export default Layout;
