import styles from "./page.module.css";

import { PageProvider } from "./page-context";

import {Button} from "@/components/Buttons";
import {Navigation, Message, Document, Logo} from "@/components/Icons";
import Menu from "./page-menu.jsx";
import Chat from "./page-chat.jsx";

export default function Home() {
  
  return (
    <PageProvider>
      <div className={styles.page}>
        <aside>
          <Menu />
        </aside>
        <main className={styles.main}>
          <header>
            <Button style="primary" icon={Message}>Chat</Button>
            <Button style="secondary" icon={Document}>Revue de presse</Button>
          </header>
          <section>
            <Chat />
          </section>
          <footer>
            <textarea placeholder="Tapez votre message ici..."></textarea>
            <Button style="primary" disabled icon={Navigation}></Button>
          </footer>
        </main>
      </div>
    </PageProvider>
  );
}
