import { memo } from 'react';
import styles from './BaseCard.module.css';

/**
 * @param {string} width - largeur de la boite (CSS)
 * @param {string} height - hauteur de la boite (CSS)
 */
const BaseCard = ({
  className="",
  width="auto",
  height="auto",
  as = "article",
  children,
  ...props
}) => {

  const BaseType = as;

  return (
    <BaseType className={`${styles.container} ${className}`} style={{ width, height }}>
        {children}
    </BaseType>
  );
};

export default memo(BaseCard);