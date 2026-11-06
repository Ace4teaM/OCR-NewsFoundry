"use client";

import {Button} from "@/components/Buttons";
import { useAppContext } from "@/contexts/AppContext";

export default function CopyButton({data}) {
    
  const { setNotification } = useAppContext();

  // paramètres
  const { 
    text = ""
  } = data;

    async function copyToClipboard(text) {
        await navigator.clipboard.writeText(text);

        setNotification("Revue copiée !")
    }

  return (
    <Button onClick={(e)=>copyToClipboard(data.text)} style="secondary">Copier</Button>
  );
}