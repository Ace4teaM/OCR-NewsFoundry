import { useRef, useEffect } from "react";
import styles from "./Revues.module.css";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {Calendar} from "lucide-react";
import CopyButton from "./CopyButton";

/**
 * Formate une date en français.
 * Exemple : mardi 30 septembre 2025 à 09:00
 * @param {string|Date} date
 * @returns {string}
 */
function formatLongDate(date) {
    return new Intl.DateTimeFormat("fr-FR", {
        weekday: "long",
        day: "numeric",
        month: "long",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        hourCycle: "h23"
    })
    .format(new Date(date))
    .replace(" à ", " à ");
}

/**
 * Retourne le numéro de semaine ISO.
 * Exemple : Semaine 39
 * @param {string|Date} date
 * @returns {string}
 */
function formatWeek(date) {
    const d = new Date(date);

    const utc = new Date(Date.UTC(
        d.getFullYear(),
        d.getMonth(),
        d.getDate()
    ));

    const day = utc.getUTCDay() || 7;

    utc.setUTCDate(utc.getUTCDate() + 4 - day);

    const yearStart = new Date(Date.UTC(
        utc.getUTCFullYear(), 0, 1
    ));

    const week = Math.ceil(
        ((utc - yearStart) / 86400000 + 1) / 7
    );

    return `Semaine ${week}`;
}

export default function Revues({data, children}) {

  // paramètres
  const { 
    items = [
        {
            "date":"2025-09-30 09:00",
            "theme": "Politiques",
            "content": `**REVUE DE PRESSE POLITIQUE - 30 Septembre 2025**

**Synthèse hebdomadaire des principales actualités politiques :**

• **Réforme économique** : Le gouvernement a présenté son plan de relance économique avec des mesures ciblées sur l'emploi et l'innovation. Les réactions sont mitigées entre opposition et majorité.

• **Relations internationales** : Préparation du sommet européen avec focus sur les questions énergétiques et la coopération en matière de défense.

• **Politique intérieure** : Débats parlementaires sur la réforme du système de santé, avec des amendements proposés par différents groupes politiques.

**Perspectives** : Les prochaines semaines seront cruciales pour l'adoption des mesures proposées et leur impact sur l'opinion publique.`
        },
        {
            "date":"2025-09-30 09:00",
            "theme": "Politiques",
            "content": `**REVUE DE PRESSE POLITIQUE - 30 Septembre 2025**

**Synthèse hebdomadaire des principales actualités politiques :**

• **Réforme économique** : Le gouvernement a présenté son plan de relance économique avec des mesures ciblées sur l'emploi et l'innovation. Les réactions sont mitigées entre opposition et majorité.

• **Relations internationales** : Préparation du sommet européen avec focus sur les questions énergétiques et la coopération en matière de défense.

• **Politique intérieure** : Débats parlementaires sur la réforme du système de santé, avec des amendements proposés par différents groupes politiques.

**Perspectives** : Les prochaines semaines seront cruciales pour l'adoption des mesures proposées et leur impact sur l'opinion publique.`
        }
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
    <div className={styles.content} ref={containerRef}>
        <div className={styles.header}>
            <h2>Revues de presse</h2>
            <p>Consultez et gérez vos revues de presse générées par l'IA</p>
        </div>

        {!items || items.length === 0 &&
            <p>Vous n'avez aucune revue de presse, pour commencer créez-en une partir d'un chat.</p>
        }

        {items && items.length > 0 && items.map((item, index) => (
            <div key={index} className={styles.box}>
                <div className={styles.infos}>
                    <div className={styles.title}>Actualités {item.theme} - {formatWeek(item.created_at)}</div>
                    <div className={styles.date}><Calendar size={14} />&nbsp;{formatLongDate(item.created_at)}</div>
                    <div className={styles.topRight}>
                    <CopyButton data={{text: item.content}} />
                    </div>
                </div>
                <div className={styles.text}>
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{item.content}</ReactMarkdown>
                </div>
            </div>
        ))}
    </div>
  );
}