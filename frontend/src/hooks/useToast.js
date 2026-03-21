import { createContext, useContext, useState, useCallback, useRef } from 'react';

const ToastContext = createContext(null);

let toastId = 0;

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) throw new Error('useToast must be used within ToastProvider');
  return context;
}

export function useToastState() {
  const [toasts, setToasts] = useState([]);
  const timersRef = useRef({});

  const removeToast = useCallback((id) => {
    clearTimeout(timersRef.current[id]);
    delete timersRef.current[id];
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = useCallback((message, type = 'success') => {
    const id = ++toastId;
    setToasts((prev) => [...prev, { id, message, type }]);
    timersRef.current[id] = setTimeout(() => removeToast(id), 3000);
    return id;
  }, [removeToast]);

  const toast = useCallback((message) => addToast(message, 'success'), [addToast]);
  toast.success = (message) => addToast(message, 'success');
  toast.error = (message) => addToast(message, 'error');
  toast.info = (message) => addToast(message, 'info');

  return { toasts, toast, removeToast };
}

export { ToastContext };
