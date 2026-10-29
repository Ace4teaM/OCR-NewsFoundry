import styles from "./page.module.css";

import { PageProvider } from "./page-context";

import Menu from "./page-menu.jsx";
import Chat from "./page-chat.jsx";
import Actions from "./page-actions.jsx";
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
  );
}
