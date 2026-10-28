"use client"

import { useRef, useId, useState, useEffect } from 'react';
import styles from './ModalDialog.module.css'
import {BaseCard} from "@/components/Cards";
import {X} from "lucide-react";

const ModalDialog = ({
    Component,
    ComponentProps = {},
    closeDialog= (result)=>{},
    ...props
}) => {

  const [closeConfirmMessage, setCloseConfirmMessage] = useState(null)

  const [dialogResult, setDialogResult] = useState(null)

  const onCloseDialog= ()=>{
    if(!closeConfirmMessage || (closeConfirmMessage && confirm(closeConfirmMessage)))
      return true;
    return false;
  }

  useEffect(()=>{
    if(dialogResult === true || dialogResult === false)
    {
      const dlg = document.getElementById(dialog_id);
      dlg.close();
    }
  },[dialogResult])
    
  const dialog_id = useId();

  const onClickClose = (e) => {
    if(onCloseDialog && !onCloseDialog())
      return;

    const dlg = document.getElementById(dialog_id);
    dlg.close();
  }

  const isInDialogRef = useRef(false)

  const handleMouseUp = (e) => {
    if (isInDialogRef.current) {
      return
    }

    if(onCloseDialog && !onCloseDialog())
      return;

    const dlg = document.getElementById(dialog_id);
    dlg.close();
  }

  const handleMouseDown = (e) => {
    const dlg = document.getElementById(dialog_id);
    const rect = dlg.getBoundingClientRect();

    const clickedInDialog =
      rect.top <= e.clientY &&
      e.clientY <= rect.bottom &&
      rect.left <= e.clientX &&
      e.clientX <= rect.right;

    isInDialogRef.current = clickedInDialog;
  }

  return (
    <dialog id={dialog_id} className={styles.container} onMouseUp={handleMouseUp} onMouseDown={handleMouseDown} onClose={(e)=>closeDialog(dialogResult)} {...props}>
      <BaseCard className={styles.content}>
         <span className={styles.closeBtn} onClick={onClickClose}><X></X></span>
         <Component {...ComponentProps} setDialogResult={setDialogResult} setCloseConfirmMessage={setCloseConfirmMessage} />
      </BaseCard>
    </dialog>
  )
}

export default ModalDialog;
