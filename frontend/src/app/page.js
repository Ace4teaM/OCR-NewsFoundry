import styles from "./page.module.css";

import { PageProvider } from "./page-context";

import {Button} from "@/components/Buttons";
import { Message, Document } from "@/components/Icons";
import Menu from "./page-menu.jsx";
import Chat from "./page-chat.jsx";
import Prompt from "./page-prompt.jsx";

export default async function Home({ searchParams }) {
  const params = await searchParams;

  return (
    <PageProvider searchParams={params}>
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
            <Prompt />
          </footer>
        </main>
      </div>
    </PageProvider>
  );
}
