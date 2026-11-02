import styles from "./page.module.css";
import { Suspense } from "react";
import { PageProvider } from "./page-context";

import Menu from "./page-menu.jsx";
import Chat from "./page-chat.jsx";
import Actions from "./page-actions.jsx";
import Prompt from "./page-prompt.jsx";

export default async function Home() {
  return (
    <Suspense fallback={<div>Chargement...</div>}>
      <PageProvider>
        <div className={styles.page}>
          <aside>
            <Menu />
          </aside>
          <main className={styles.main}>
            <header>
              <Actions />
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
    </Suspense>
  );
}
