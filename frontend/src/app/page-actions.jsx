"use client"

import { usePageContext } from "./page-context.jsx";

import { useRouter } from "next/navigation";

import {Button} from "@/components/Buttons";
import { Message, Document } from "@/components/Icons";

export default function Component() {
  const { setSelectedItem } = usePageContext();
  const router = useRouter();

  return (
    <>
        <Button style="primary" icon={Message} onClick={() => setSelectedItem(null)}>Chat</Button>
        <Button style="secondary" icon={Document} onClick={() => router.push("/revue-de-presse")}>Revue de presse</Button>
    </>
  );
}
