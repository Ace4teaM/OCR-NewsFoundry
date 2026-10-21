import styles from "./page.module.css";

import {Button} from "@/components/Buttons";
import {LogoLarge} from "@/components/Icons";


export default function Page() {
  return (
    <div className={styles.page}>
      <main className={styles.main}>
        <div className={styles.box}>
            <LogoLarge className={styles.icon}/>
            <p>Connectez-vous pour accéder à votre assistant d'actualités IA</p>
            <form>
                <label htmlFor="mail">Adresse email</label>
                <input type="mail" name="mail" placeholder="votre.email@exemple.com" />
                <Button type="submit" style="secondary">Se connecter</Button>
            </form>
        </div>
      </main>
    </div>
  );
}
