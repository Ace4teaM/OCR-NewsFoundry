"use client"

import { usePageContext } from "./page-context.jsx";

import Chat from "@/components/Chat/Chat";
import Revues from "@/components/Revues/Revues";

export default function Component() {
  const { messages, revues, contentView } = usePageContext();

  return (
      contentView === "revues" ? (
          <Revues
              data={{
                  items: revues
              }}
          />
      ) : (
          <Chat
              data={{
                  items: messages
              }}
          />
      )
  );
}
