"use client";

import { createContext, useContext, useEffect, useState, useRef } from "react";
import {ModalDialog} from "@/components/Containers";
import ErrorNotification from "@/components/ErrorNotification/ErrorNotification";

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const [theme, setTheme] = useState("light");
  const [dialog, setDialog] = useState(null);
  const dialogRef = useRef(null);
  const [ error, setError ] = useState(null)


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

  return (
    <AppContext.Provider
      value={{
        theme,
        setTheme,
        openDialog,
        closeDialog,
        setError,
        error,
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