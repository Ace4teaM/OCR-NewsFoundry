import { useRef, useEffect } from "react";
import styles from "./Chat.module.css";
import { Logo, User } from "@/components/Icons";


/**
 * Formate une date de manière minimaliste.
 * Aujourd'hui : HH:mm
 * Hier : hier à HH:mm
 * Avant-hier et avant : le JJ/MM à HH:mm
 * @param {string | Date} value - Date à formater.
 * @returns {string} Date formatée.
 */
function formatDateTime(value) {
    const date = new Date(value);
    const now = new Date();

    const time = date.toLocaleTimeString("fr-FR", {
        hour: "2-digit",
        minute: "2-digit",
    });

    const startOfDay = (d) =>
        new Date(d.getFullYear(), d.getMonth(), d.getDate());

    const diffDays = Math.round(
        (startOfDay(now) - startOfDay(date)) / 86400000
    );

    if (diffDays === 0) {
        return time;
    }

    if (diffDays === 1) {
        return `hier à ${time}`;
    }

    const dayMonth = date.toLocaleDateString("fr-FR", {
        day: "2-digit",
        month: "2-digit",
    });

    return `le ${dayMonth} à ${time}`;
}


export default function Chat({data, children}) {

  // paramètres
  const { 
    items = [
        {
            "date":"10:31",
            "message": "Peux-tu me donner les dernières actualités politiques ?",
        },
        {
            "date":"10:31",
            "response": `Voici un résumé des dernières nouvelles politiques :

• Le gouvernement a annoncé de nouvelles mesures économiques
• Débat sur la réforme des retraites au Parlement
• Visite diplomatique prévue la semaine prochaine

Souhaitez-vous que je génère une revue de presse détaillée sur l'un de ces sujets ?`
        },
        {
            "date":"10:32",
            "message": `Je suis particulièrement curieux des applications 
dans le domaine de la santé et de l'éducation.`
        },
    ]
  } = data;

    const containerRef = useRef(null);

    useEffect(() => {
        const element = containerRef.current;

        if (element) {
            element.scrollTo({
                top: element.scrollHeight,
                behavior: "smooth",
            });
        }
    }, [items]);

  return (
    !items || items.length === 0 ? 
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
        :
        <div className={styles.content} ref={containerRef}>
            {items.map((item, index) => (
                <div key={index} className={styles.message} data-type={item.message ? "user" : "system"}>
                    <div className={styles.text}>{item.message ?? item.response}</div>
                    <div className={styles.date}>{formatDateTime(item.date)}</div>
                    <div className={styles.icon}>{item.message ? <User /> : <Logo />}</div>
                </div>
            ))}
        </div>
  );
}