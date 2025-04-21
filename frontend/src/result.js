


const pdf = (flag) => {
    if(flag === 0){
        fetch("http://localhost:8000/result/summary")
        .then(response => {
            response.blob().then(blob => {
                let url = window.URL.createObjectURL(blob);
                let a = document.createElement('a');
                a.href = url;
                a.download = "summary.pdf";

                a.click();
                a.remove();
            });
            
    });
}
    else {
        fetch("http://localhost:8000/result/transcript")
        .then(response => {
            response.blob().then(blob => {
                let url = window.URL.createObjectURL(blob);
                let a = document.createElement('a');
                a.href = url;
                a.download = "transcript.pdf";

                a.click();
                a.remove();
            });
            
    });
    }
}

const Result = (text)=>{ 
    
    
      
return (
    <div className = "text">
    <h1>Key TimeStamps</h1>
    <div dangerouslySetInnerHTML={{ __html: text }} /> 
    <div className='button'>
    <button onClick={()=>{pdf(0);}}>Download Summary</button>
    <button onClick= {()=> {pdf(1);}}>Download Transcript</button>
    </div>
    </div>
    )};
export default Result;