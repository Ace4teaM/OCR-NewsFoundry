import { LogoLarge } from "@/components/Icons";
import DisconnectButton from "./DisconnectButton";
import MenuItem from "./MenuItem";
import styles from "./Menu.module.css";

export default function Menu({data, setSelectedItem, selectedItem, isLogged, logoutAction, loginAction, children}) {

  // paramètres
  const { 
    items = [
        {
            "title":"Discussion du",
            "created_at": "2026-11-13T09:28:25.688451+00:00"
        },
        {
            "title":"Discussion du",
            "created_at": "2026-11-13T09:28:25.688451+00:00"
        },
        {
            "title":"Discussion du",
            "created_at": "2026-11-13T09:28:25.688451+00:00"
        },
        {
            "title":"Discussion du",
            "created_at": "2026-11-13T09:28:25.688451+00:00"
        },
        {
            "title":"Discussion du",
            "created_at": "2026-11-13T09:28:25.688451+00:00"
        },
        {
            "title":"Discussion du",
            "created_at": "2026-11-13T09:28:25.688451+00:00"
        }
    ]
  } = data;

  return (
    <nav className={styles.menu}>
        <header><a href="/"><LogoLarge className={styles.logo} /></a></header>
        <section>
            {items &&
            <ul>
                {items.map((item, index) => (
                    <MenuItem key={index} data={item} onSelect={setSelectedItem} />
                ))}
            </ul>
            }
        </section>
        <footer><DisconnectButton data={{isLogged, logoutAction, loginAction}} /></footer>
    </nav>
  );
}