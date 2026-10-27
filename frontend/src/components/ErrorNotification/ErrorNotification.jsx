"use client";

import { useEffect } from "react";
import styles from "./ErrorNotification.module.css";

/**
 * Affiche une notification d'erreur temporaire.
 *
 * @param {Object} props
 * @param {string} props.message - Message d'erreur à afficher.
 * @param {Function} props.onClose - Fonction appelée à la fermeture.
 * @param {number} [props.duration=5000] - Durée d'affichage en millisecondes.
 * @returns {JSX.Element|null}
 */
export default function ErrorNotification({
  message,
  onClose,
  duration = 5000,
}) {
  useEffect(() => {
    if (!message) {
      return;
    }

    const timeoutId = setTimeout(onClose, duration);

    return () => clearTimeout(timeoutId);
  }, [message, onClose, duration]);

  if (!message) {
    return null;
  }

  return (
    <div
      className={styles.notification}
      role="alert"
      aria-live="assertive"
    >
      <div className={styles.content}>
        <strong>Erreur</strong>
        <p>{message}</p>
      </div>

      <button
        type="button"
        className={styles.close}
        onClick={onClose}
        aria-label="Fermer la notification"
      >
        &times;
      </button>
    </div>
  );
}