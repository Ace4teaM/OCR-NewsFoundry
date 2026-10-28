"use client";

import styles from "./Menu.module.css";

export default function MenuItem({data, onSelect = () => console.log("Selection"), ...props}) {
    
  // paramètres
  const { 
    title,
    created_at
  } = data;

  return (
    <li onClick={(e)=>onSelect(data)} {...props}>
        <span>{title}</span>
        <span className={styles.created_at}>{created_at}</span>
    </li>
  );
}