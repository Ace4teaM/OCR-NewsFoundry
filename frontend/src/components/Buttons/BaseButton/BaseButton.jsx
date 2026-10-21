"use client"

import { memo } from 'react';
import styles from './BaseButton.module.css';

/**
 * @param {string} className - classe de style
 */
const BaseButton = ({
  className="",
  as = "button",
  onClick,
  children,
  ...props
}) => {

  const BaseType = as;
  
  // surcharge le onClick pour les composants dérivés
  const handleClick = (e) => {
    if (onClick) {
      onClick(e);
    }
  };


  return (
    <BaseType className={`${styles.container} ${className}`} onClick={handleClick} {...props}>
      {children}
    </BaseType>
  );
};

export default memo(BaseButton);