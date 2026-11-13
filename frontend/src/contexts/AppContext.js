"use client";

import { createContext, useContext, useEffect, useState, useRef } from "react";
import {ModalDialog} from "@/components/Containers";
import ErrorNotification from "@/components/ErrorNotification/ErrorNotification";
import InfoNotification from "@/components/InfoNotification/InfoNotification";
import { fetchApi } from "@/utils/http";
import { useRouter } from "next/navigation";

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const [theme, setTheme] = useState("light");
  const [dialog, setDialog] = useState(null);
  const dialogRef = useRef(null);
  const [ error, setError ] = useState(null)
  const [ notification, setNotification ] = useState(null)
  const [user, setUser] = useState(undefined);
  const [loading, setLoading] = useState(true);
  const firstAuth = useRef(null);
  const router = useRouter();

  function openDialog(Component, props = {}, success = () => {}, resolve = (result) => {}) {
      setDialog({
          Component,
          props,
          success,
          resolve
      });
  }

  function closeDialog(result) {
    if(result === true)
      dialog.success()
    dialog.resolve(result)
    setDialog(null);
  }

  useEffect(()=>{
    if(dialog === null)
      return;
    
    var dialogInst = dialogRef.current;
    dialogInst.showModal();

  },[dialog])

  useEffect(()=>{
    // non authentifié
    if(user === null && window.location.pathname !== "/login")
    {
      // Redirection vers l'accueil
      router.replace("/login");
    }
  },[user])

  useEffect(() => {
      if (firstAuth.current !== null)
          return;
      firstAuth.current = true;
      
      async function checkAuth() {
          try {
              const result = await fetchApi("/me");

              if (result?.success) {
                  setUser(result.data);
              } else {
                  setUser(null);
              }
          } catch (error) {
              console.error("Erreur vérification authentification", error);
              setUser(undefined);
          } finally {
              setLoading(false);
          }
      }

      checkAuth();
  }, []);

  const isLogged = !!user;

  return (
    <AppContext.Provider
      value={{
        theme,
        setTheme,
        openDialog,
        closeDialog,
        setError,
        error,
        setNotification,
        notification,
        user,
        setUser,
        isLogged,
        loading
      }}
    >
      {children}
      {dialog && (
      <ModalDialog ref={dialogRef} closeDialog={closeDialog} Component={dialog.Component} ComponentProps={dialog.props}>
      </ModalDialog>
      )}
      {error && (
      <ErrorNotification
          message={error}
          onClose={() => setError(null)}
      />
      )}
      {notification && (
      <InfoNotification
          message={notification}
          onClose={() => setNotification(null)}
      />
      )}
    </AppContext.Provider>
  );
}

export function useAppContext() {
  return useContext(AppContext);
}