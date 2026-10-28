import styles from "./page.module.css";

import {Button} from "@/components/Buttons";
import {Navigation, Message, Document, Logo} from "@/components/Icons";
import Menu from "./page-menu.jsx";
import { PageProvider } from "./page-context";

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
            <div className={styles.box}>
                <Logo className={styles.icon}/>
                <h2>Assistant Revue de Presse IA</h2>
                <p>Posez-moi des questions sur l'actualité récente ou demandez-moi de générer une revue de presse sur un sujet spécifique.</p>
                <div>Exemples:</div>
                <ul>
                    <li>"Quelles sont les dernières nouvelles en politique ?"</li>
                    <li>"Génère une revue de presse sur la technologie"</li>
                    <li>"Résume l'actualité économique de la semaine"</li>
                </ul>
            </div>
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
