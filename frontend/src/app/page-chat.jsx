"use client"

import { usePageContext } from "./page-context.jsx";

import Chat from "@/components/Chat/Chat";

export default function Component() {
  const { messages } = usePageContext();

  return (
    <Chat 
        data={{
            items: messages
        }}
    />
  );
}
