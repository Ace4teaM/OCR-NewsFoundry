"use client"

import { usePageContext } from "./page-context.jsx";
import { useAppContext } from "@/contexts/AppContext";

import Menu from "@/components/Menu/Menu";


export default function Component() {
  const { selectedItem, setSelectedItem, items, logoutAction, loginAction } = usePageContext();

  const { isLogged } = useAppContext();

  return (
    <Menu 
        data={{
            items
        }}
        setSelectedItem={setSelectedItem}
        selectedItem={selectedItem}
        logoutAction={logoutAction}
        loginAction={loginAction}
        isLogged={isLogged}
    />
  );
}
