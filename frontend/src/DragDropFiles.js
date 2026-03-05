import { useRef, useState} from "react";
import './App.css'
import Result from "./result";


    
 
const DragDropFiles = () => {
    const [files, setFiles] = useState(null);
    const [upload, setupload] = useState(null);
    const [result, setresult] = useState(null);
    const[text, setText] = useState("");
    const inputRef = useRef();
    const handleDragOver = (event) =>{
        event.preventDefault();
    };
    const handleDrop = (event) => {
        event.preventDefault();
        setFiles(event.dataTransfer.files[0])
    };
    const handleClick = async(event) =>{
        event.preventDefault();
        setupload(files);
        console.log("please wait while we summarize your file");
        const formData = new FormData();
        formData.append("file",files);
        try {
        const endpoint = "/upload/"
        const response = await fetch(endpoint,{
            method: "POST",
            body: formData
        });
        if (response.ok){setresult(files); console.log("file processed");}
        else {console.log("file not processed");}
        }
        catch(error){
        console.log(error);
        }
        };
        const gettext = async () => {
                try {
                  const response = await fetch('/result/highlights/');
                  const data = await response.text(); // use .text() because it's plain text
                  setText(data);
                } catch (error) {
                  console.error('Error fetching text:', error);
                }
              };
    

    if (files && !upload && !result) return (
        <div className="uploads">
            <p>
                {files.name}
            </p>
            <div className="actions">
                <button onClick={() => setFiles(null)}>Cancel</button>
                <button onClick={handleClick }>Upload</button>
            </div>
        </div>
    )
    else if(files && upload && !result) return (
        <div className="processing">
            <h1>Please wait while we process your files...</h1>
            <div className="spinner" />
        </div>
    )
    else if (files && result) return (
        <div>{
            gettext() &&
            Result(text)
               }</div>
        
        )

    return (
        <>
        {!files &&(
            


            <div 
                className="dropzone"
                onDragOver={handleDragOver}
                onDrop={handleDrop}
            >
                <h1> Drag and Drop Files to Upload</h1>
                <h1>OR</h1>
                <input 
                    type="file"
                    onChange = {(event) => setFiles(event.target.files[0])}
                    hidden
                    ref={inputRef}
                />
            
                <button onClick={() => inputRef.current.click()}>Select Files</button>
            </div>
          )}
        </>
    );
};

export default DragDropFiles;