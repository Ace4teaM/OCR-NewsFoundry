"use client";

import { createContext, useContext, useEffect, useState, useRef } from "react";
import {ModalDialog} from "@/components/Containers";
import ErrorNotification from "@/components/ErrorNotification/ErrorNotification";
import { fetchApi } from "@/utils/http";

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const [theme, setTheme] = useState("light");
  const [dialog, setDialog] = useState(null);
  const dialogRef = useRef(null);
  const [ error, setError ] = useState(null)
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

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

  useEffect(() => {
      async function checkAuth() {
          try {
              const result = await fetchApi("me");

              if(result.success == false)
              {
                  console.info("utilisateur non authentifié");
                  setUser(null);
                  return;
              }

              console.info("utilisateur authentifié");
              setUser(result.data);
          } catch (error) {
              console.error("erreur vérif authentifié", error);
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
          duration={5000}
      />
      )}
    </AppContext.Provider>
  );
}

export function useAppContext() {
  return useContext(AppContext);
}