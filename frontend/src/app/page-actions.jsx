"use client"

import { usePageContext } from "./page-context.jsx";

import {Button} from "@/components/Buttons";
import { Message, Document } from "@/components/Icons";
import { MoveLeft } from "lucide-react";
import styles from "./page.module.css";

export default function Component() {
  const { createRevue, selectedItem, contentView, setContentView, createChat } = usePageContext();

  return (
    selectedItem === null ? (
    <div className={styles.revuesContent}>
        <Button style={contentView === "chat" ? "primary" : "secondary"} icon={Message} onClick={(e) => createChat()}>Chat</Button>
        <Button style={contentView === "revues" ? "primary" : "secondary"} icon={Document} onClick={(e) => setContentView("revues")}>Revue de presse</Button>
    </div>
    ) : 
    (
    <div className={styles.chatContent}>
        <div className={styles.back}>
          <MoveLeft />
          <a href="/">
            <div className={styles.backTitle}>{selectedItem.title}</div>
            <div className={styles.backLabel}>Conversation active</div>
          </a>
        </div>
        <Button style="primary" icon={Document} onClick={(e) => createRevue()}>Générer une revue de presse</Button>
    </div>
    )
  );
}
