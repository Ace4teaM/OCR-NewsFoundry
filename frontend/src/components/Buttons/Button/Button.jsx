import { memo } from 'react';
import styles from './Button.module.css';
import {BaseButton} from '@/components/Buttons'

/**
 * Composant de bouton personnalisable
 * @param {className} Nom de la classe en remplacement de la classe par défaut
 * @param {children} Contenu du bouton
 * @param {style} Style du bouton (primary ou secondary) passé à l'attribut `data-style` du bouton
 * @param {icon} Icône à afficher dans le bouton, null si aucune
 */
const Button = ({
  className = null,
  children,
  style = "primary", // ou secondary
  icon = null,
  color="currentColor",
  ...props
}) => {

  const Icon = icon;

  return (
    <BaseButton
      className={className ?? styles.container}
      data-style={style}
      color={color}
      {...props}
    >
      {Icon && <Icon className={styles.icon} color={color} />}
      {children && <span className={styles.children}>{children}</span>}
    </BaseButton>
  );
};

export default memo(Button);