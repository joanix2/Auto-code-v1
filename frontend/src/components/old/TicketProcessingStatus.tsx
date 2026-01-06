/**
 * TicketProcessingStatus Component
 * Displays real-time status of ticket processing with progress bar
 */

import React from "react";
import { useTicketProcessing } from "../hooks/useTicketProcessing";

interface TicketProcessingStatusProps {
  ticketId: string;
  onComplete?: () => void;
  onError?: (error: string) => void;
}

export const TicketProcessingStatus: React.FC<TicketProcessingStatusProps> = ({ ticketId, onComplete, onError }) => {
  const { status, message, step, progress, error, logs, isConnected } = useTicketProcessing(ticketId);

  // Trigger callbacks
  React.useEffect(() => {
    if (status === "COMPLETED" && onComplete) {
      onComplete();
    }
    if (status === "FAILED" && error && onError) {
      onError(error);
    }
  }, [status, error, onComplete, onError]);

  const getStatusColor = () => {
    switch (status) {
      case "PENDING":
        return "bg-yellow-500";
      case "IN_PROGRESS":
        return "bg-blue-500";
      case "COMPLETED":
        return "bg-green-500";
      case "FAILED":
      case "CANCELLED":
        return "bg-red-500";
      default:
        return "bg-gray-500";
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case "PENDING":
      case "IN_PROGRESS":
        return (
          <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        );
      case "COMPLETED":
        return (
          <svg className="h-5 w-5 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
        );
      case "FAILED":
      case "CANCELLED":
        return (
          <svg className="h-5 w-5 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
              clipRule="evenodd"
            />
          </svg>
        );
      default:
        return null;
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Traitement Automatique</h3>
        <div className={`px-3 py-1 rounded-full flex items-center space-x-2 ${getStatusColor()}`}>
          {getStatusIcon()}
          <span className="text-white text-sm font-medium">{status}</span>
        </div>
      </div>

      {/* Connection Status */}
      {!isConnected && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3">
          <p className="text-sm text-yellow-800">⚠️ WebSocket déconnecté - Reconnexion en cours...</p>
        </div>
      )}

      {/* Progress Bar */}
      {progress !== undefined && (
        <div>
          <div className="flex justify-between mb-1">
            <span className="text-sm font-medium text-gray-700">Progression</span>
            <span className="text-sm font-medium text-gray-700">{progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div className={`h-2.5 rounded-full transition-all duration-300 ${getStatusColor()}`} style={{ width: `${progress}%` }}></div>
          </div>
        </div>
      )}

      {/* Current Step */}
      {step && (
        <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
          <p className="text-sm text-blue-800">
            <span className="font-semibold">Étape actuelle:</span> {step}
          </p>
        </div>
      )}

      {/* Status Message */}
      <div className="bg-gray-50 rounded-md p-3">
        <p className="text-sm text-gray-700">{message}</p>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-3">
          <p className="text-sm text-red-800">
            <span className="font-semibold">Erreur:</span> {error}
          </p>
        </div>
      )}

      {/* Logs */}
      {logs.length > 0 && (
        <div className="mt-4">
          <h4 className="text-sm font-semibold text-gray-700 mb-2">Journal d'activité</h4>
          <div className="bg-gray-900 rounded-md p-3 max-h-60 overflow-y-auto font-mono text-xs">
            {logs.map((log, index) => (
              <div key={index} className={`mb-1 ${log.level === "ERROR" ? "text-red-400" : log.level === "WARNING" ? "text-yellow-400" : log.level === "INFO" ? "text-green-400" : "text-gray-400"}`}>
                <span className="text-gray-500">[{log.level}]</span> {log.message}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
