"use client"

import { usePageContext } from "./page-context.jsx";

import Menu from "@/components/Menu/Menu";


export default function Component() {
  const { selectedItem, setSelectedItem, items } = usePageContext();

  return (
    <Menu 
        data={{
            items
        }}
        setSelectedItem={setSelectedItem}
        selectedItem={selectedItem}
    />
  );
}
