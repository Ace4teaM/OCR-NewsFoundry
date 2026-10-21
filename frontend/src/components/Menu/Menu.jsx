import { LogoLarge } from "@/components/Icons";
import DisconnectButton from "./DisconnectButton";
import styles from "./Menu.module.css";

export default function Menu({data, children}) {
    
  // paramètres
  const { 
    title = "newsfoundry",
    items = [
        {
            "title":"Discussion du",
            "date": "2026-10-12"
        },
        {
            "title":"Discussion du",
            "date": "2026-10-12"
        },
        {
            "title":"Discussion du",
            "date": "2026-10-12"
        },
        {
            "title":"Discussion du",
            "date": "2026-10-12"
        },
        {
            "title":"Discussion du",
            "date": "2026-10-12"
        },
        {
            "title":"Discussion du",
            "date": "2026-10-12"
        }
    ],
    disconnectAction
  } = data;

  return (
    <nav className={styles.menu}>
        <header><LogoLarge className={styles.logo} /></header>
        <section>
            <ul>
                {items.map((item, index) => (
                    <li key={index}>
                        <span>{item.title}</span>
                        <span className={styles.date}>{item.date}</span>
                    </li>
                ))}
            </ul>
        </section>
        <footer><DisconnectButton data={{disconnectAction}} /></footer>
    </nav>
  );
}