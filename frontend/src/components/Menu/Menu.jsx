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
            "created_at": "2026-10-12"
        },
        {
            "title":"Discussion du",
            "created_at": "2026-10-12"
        },
        {
            "title":"Discussion du",
            "created_at": "2026-10-12"
        },
        {
            "title":"Discussion du",
            "created_at": "2026-10-12"
        },
        {
            "title":"Discussion du",
            "created_at": "2026-10-12"
        },
        {
            "title":"Discussion du",
            "created_at": "2026-10-12"
        }
    ]
  } = data;

  return (
    <nav className={styles.menu}>
        <header><LogoLarge className={styles.logo} /></header>
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