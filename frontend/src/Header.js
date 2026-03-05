
import { useEffect,useState,useContext,createContext } from "react";
const Headercontext = createContext({
    msg:"", fetchmsg: () => {}
  })

export default function Header()
{

    
    const [msg,setmsg] = useState(null);
    const fetchmsg = async () => {
        //const apiUrl = process.env.NODE_ENV === 'production' ? window.location.origin: 'http://127.0.0.1:8000'; 
        const resp = await fetch("http://localhost:8000/"); 
        const sent = await resp.json()
        setmsg(sent.data)
    }
    useEffect(()=>{fetchmsg()},[])    
    return (
        <Headercontext.Provider value={{msg,fetchmsg}}>
          
            <h1>{msg}</h1>
         
            

        </Headercontext.Provider>
    )
}