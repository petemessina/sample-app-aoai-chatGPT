import { DocumentStatusState } from '../api'
import { Action, AppState } from './AppProvider'

// Define the reducer function
export const appStateReducer = (state: AppState, action: Action): AppState => {
  switch (action.type) {
    case 'TOGGLE_CHAT_HISTORY':
      return { ...state, isChatHistoryOpen: !state.isChatHistoryOpen, isUploadedDocumentsOpen: false }
    case 'TOGGLE_DOCUMENT_LIST':
      return { ...state, isUploadedDocumentsOpen: !state.isUploadedDocumentsOpen, isChatHistoryOpen: false }
    case 'UPDATE_CURRENT_CHAT':
      return { ...state, currentChat: action.payload }
    case 'UPDATE_CHAT_HISTORY_LOADING_STATE':
      return { ...state, chatHistoryLoadingState: action.payload }
    case 'UPDATE_UPLOADED_DOCUMENTS_LOADING_STATE':
      return { ...state, uploadedDocumentsLoadingState: action.payload }
    case 'UPDATE_CHAT_HISTORY':
      if (!state.chatHistory || !state.currentChat) {
        return state
      }
      const conversationIndex = state.chatHistory.findIndex(conv => conv.id === action.payload.id)
      if (conversationIndex !== -1) {
        const updatedChatHistory = [...state.chatHistory]
        updatedChatHistory[conversationIndex] = state.currentChat
        return { ...state, chatHistory: updatedChatHistory }
      } else {
        return { ...state, chatHistory: [...state.chatHistory, action.payload] }
      }
    case 'UPDATE_CURRENT_CHAT_AND_HISTORY':
      if (!state.chatHistory) {
        return state
      }

      const existingChatIndex = state.chatHistory.findIndex(conv => conv.id === action.payload.id)

      if (existingChatIndex !== -1) {
        return state;
      }
      
      return { ...state, currentChat: action.payload, chatHistory: [...state.chatHistory, action.payload] }
    case 'UPDATE_UPLOADED_DOCUMENTS':
      if (!state.uploadedDocuments) {
        return state
      }

      const uploadedDocumentIndex = state.uploadedDocuments.findIndex(conv => conv.id === action.payload.id)
      
      if (uploadedDocumentIndex !== -1) {
        const updatedChatHistory = [...state.uploadedDocuments]
        updatedChatHistory[uploadedDocumentIndex] = action.payload

        return { ...state, uploadedDocuments: updatedChatHistory }
      } else {
        return { ...state, uploadedDocuments: [...state.uploadedDocuments, action.payload] }
      }
    case 'UPDATE_PENDING_DOCUMENTS':
      if (!state.pendingDocuments || !state.uploadedDocuments) {
        return state;
      }
    
      const currentPendingDocuments = [...state.pendingDocuments];
      const currentUploadedDocuments = [...state.uploadedDocuments];
    
      action.payload.forEach(document => {
        const pendingDocumentIndex = currentPendingDocuments.findIndex(conv => conv.id === document.id);
        const uploadedDocumentIndex = currentUploadedDocuments.findIndex(conv => conv.id === document.id);
    
        if (pendingDocumentIndex !== -1 && (document.status === DocumentStatusState.Indexed || document.status === DocumentStatusState.Failed || document.status === DocumentStatusState.PollingTimeout)) {
          currentPendingDocuments.splice(pendingDocumentIndex, 1);
        } else {
          if (pendingDocumentIndex !== -1) {
            currentPendingDocuments[pendingDocumentIndex] = document;
          } else {
            currentPendingDocuments.push(document);
          }
        }

        if (uploadedDocumentIndex !== -1) {
          currentUploadedDocuments[uploadedDocumentIndex] = document;
        } else {
          currentUploadedDocuments.push(document);
        }
      });
    
      return { ...state, pendingDocuments: currentPendingDocuments, uploadedDocuments: currentUploadedDocuments };

    case 'UPDATE_CHAT_TITLE':
      if (!state.chatHistory) {
        return { ...state, chatHistory: [] }
      }
      const updatedChats = state.chatHistory.map(chat => {
        if (chat.id === action.payload.id) {
          if (state.currentChat?.id === action.payload.id) {
            state.currentChat.title = action.payload.title
          }
          //TODO: make api call to save new title to DB
          return { ...chat, title: action.payload.title }
        }
        return chat
      })
      return { ...state, chatHistory: updatedChats }
    case 'DELETE_CHAT_ENTRY':
      if (!state.chatHistory) {
        return { ...state, chatHistory: [] }
      }

      if(!state.uploadedDocuments) {
        return { ...state, uploadedDocuments: [] }
      }

      const filteredChat = state.chatHistory.filter(chat => chat.id !== action.payload)
      const filteredDocuments = state.uploadedDocuments.filter(document => document.conversationId !== action.payload)

      state.currentChat = null
      //TODO: make api call to delete conversation from DB
      return { ...state, chatHistory: filteredChat, uploadedDocuments: filteredDocuments }
    case 'DELETE_UPLOADED_DOCUMENT':
        if (!state.uploadedDocuments) {
          return { ...state, uploadedDocuments: [] }
        }
        const filteredUploadedDocuments = state.uploadedDocuments.filter(document => document.id !== action.payload)
        return { ...state, uploadedDocuments: filteredUploadedDocuments }
    case 'DELETE_CHAT_HISTORY':
      //TODO: make api call to delete all conversations from DB
      return { ...state, chatHistory: [], uploadedDocuments: [], filteredChatHistory: [], currentChat: null }
    case 'DELETE_CURRENT_CHAT_MESSAGES':
      //TODO: make api call to delete current conversation messages from DB
      if (!state.currentChat || !state.chatHistory) {
        return state
      }
      const updatedCurrentChat = {
        ...state.currentChat,
        messages: []
      }
      return {
        ...state,
        currentChat: updatedCurrentChat
      }
    case 'FETCH_CHAT_HISTORY':
      return { ...state, chatHistory: action.payload }
    case 'FETCH_UPLOADED_DOCUMENTS':
      return { ...state, uploadedDocuments: action.payload }
    case 'SET_COSMOSDB_STATUS':
      return { ...state, isCosmosDBAvailable: action.payload }
    case 'FETCH_FRONTEND_SETTINGS':
      return { ...state, isLoading: false, frontendSettings: action.payload }
    case 'SET_FEEDBACK_STATE':
      return {
        ...state,
        feedbackState: {
          ...state.feedbackState,
          [action.payload.answerId]: action.payload.feedback
        }
      }
    case 'SET_ANSWER_EXEC_RESULT':
      return {
        ...state,
        answerExecResult: {
          ...state.answerExecResult,
          [action.payload.answerId]: action.payload.exec_result
        }
      }
    default:
      return state
  }
}
