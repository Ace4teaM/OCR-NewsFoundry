"use client";

import { Logout } from "@/components/Icons";
import styles from "./Menu.module.css";

export default function DisconnectButton({data}) {
    
  // paramètres
  const { 
    disconnectAction = () => console.log("Déconnexion")
  } = data;

  return (
    <button onClick={(e)=>disconnectAction()}><Logout /> Se déconnecter</button>
  );
}