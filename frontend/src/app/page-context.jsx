"use client";

import { createContext, useContext, useState } from "react";

const PageContext = createContext(null);

/**
 * Fournit les états partagés propres à la page.
 * @param {{ children: import("react").ReactNode }} props
 */
export function PageProvider({ children }) {
  const [ selectedItem, setSelectedItem ] = useState(null)

    return (
        <PageContext.Provider
            value={{ selectedItem, setSelectedItem }}
        >
            {children}
        </PageContext.Provider>
    );
}

/**
 * Accède aux états propres à la page.
 */
export function usePageContext() {
    const context = useContext(PageContext);

    if (context === null) {
        throw new Error("usePageContext doit être utilisé dans PageProvider");
    }

    return context;
}