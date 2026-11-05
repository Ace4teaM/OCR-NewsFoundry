"use client";

import {Button} from "@/components/Buttons";

async function copyToClipboard(text) {
    await navigator.clipboard.writeText(text);
}

export default function CopyButton({data}) {
    
  // paramètres
  const { 
    text = ""
  } = data;

  return (
    <Button onClick={(e)=>copyToClipboard(data.text)} style="secondary">Copier</Button>
  );
}