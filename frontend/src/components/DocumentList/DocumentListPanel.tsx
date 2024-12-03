import React, { useContext, useEffect, useRef, useState, useCallback } from 'react'
import {
  CommandBarButton,
  ICommandBarStyles,
  IStackStyles,
  Spinner,
  SpinnerSize,
  Stack,
  StackItem,
  Text,
} from '@fluentui/react'

import { DocumentListItem } from './DocumentListItem'
import { UploadedDocument, uploadedDocumentList, UploadedDocumentLoadingState, getDocumentStatuses, DocumentStatusState } from '../../api'
import { AppStateContext } from '../../state/AppProvider'
import styles from './DocumentListPanel.module.css'

type DocumentPolling = {
  id: string;
  pollingCount: number;
}

interface Props {
  conversationId?: string;
  handleSelectedUploadDocument: (id: string, checked:boolean) => void;
}

export enum DocumentListPanelTabs {
    Documents = 'Documents'
}

const commandBarStyle: ICommandBarStyles = {
  root: {
    padding: '0',
    display: 'flex',
    justifyContent: 'center',
    backgroundColor: 'transparent'
  }
}

export const DocumentListPanel: React.FC<Props> = ({conversationId, handleSelectedUploadDocument}) => {
  const appStateContext = useContext(AppStateContext);
  const [offset, setOffset] = useState<number>(25);
  const [maxPollingCount, setPollingCount] = useState<number>(30);
  const [observerCounter, setObserverCounter] = useState(0);
  const [filteredUploadedDocuments, setFilteredUploadedDocuments] = useState<UploadedDocument[]>([]);
  const [selectedUploadedDocuments, setSelectedUploadedDocuments] = useState<string[]>([]);
  const [pendingDocumentStatuses, setPendingDocumentStatuses] = useState<Array<UploadedDocument>>([]);
  const [isPollingForStatus, setIsPollingForStatus] = useState<boolean>(false);

  const observerTarget = useRef(null)
  const firstRender = useRef(true)

  const handleDocumentUploadClick = () => {
    appStateContext?.dispatch({ type: 'TOGGLE_DOCUMENT_LIST' })
  }

  useEffect(() => {
    if (firstRender.current && conversationId) {
      handleFetchUploadedDocuments()
      firstRender.current = false
      return
    }
    handleFetchUploadedDocuments()
    setOffset(offset => (offset += 25))
  }, [observerCounter])

  
  const documentPollingStatus = useCallback(async () => {
    if(!appStateContext?.state.pendingDocuments && appStateContext?.state.pendingDocuments?.length == 0) {
      setIsPollingForStatus(false);
      return;
    }

    const documentStatusData = await getDocumentStatuses(appStateContext?.state.pendingDocuments?.map(doc => doc.id) ?? []) ?? [];

    documentStatusData.map(document => {
      const currentPendingDocumentItem = appStateContext?.state.pendingDocuments?.find(d => d.id === document.id);

      if(currentPendingDocumentItem && currentPendingDocumentItem.pollingCount >= maxPollingCount) {
        document.status = DocumentStatusState.PollingTimeout;
      }
    });

    appStateContext?.dispatch({ type: 'UPDATE_PENDING_DOCUMENTS', payload: documentStatusData });
  }, [appStateContext?.state.pendingDocuments]);

  useEffect(() => {
    if (appStateContext?.state.pendingDocuments && appStateContext?.state.pendingDocuments.length > 0) {
      setIsPollingForStatus(true);

      const interval = setInterval(async() => {
        await documentPollingStatus();
      }, 5000);

      return () => clearInterval(interval);
    }

  }, [isPollingForStatus, appStateContext?.state.pendingDocuments, documentPollingStatus]);

  useEffect(() => {
    const missingPendingItems = appStateContext?.state.pendingDocuments?.filter(filteredItem => {
      return !pendingDocumentStatuses.some(d => d.id === filteredItem.id);
    }) ?? [];

    if(missingPendingItems.length > 0) {
      setPendingDocumentStatuses(prev => [...prev, ...missingPendingItems.map(item => ({...item, pollingCount: 0}))]);
    }
  }, [appStateContext?.state.pendingDocuments]);

  useEffect(() => {
    if(appStateContext && appStateContext.state.uploadedDocuments && appStateContext.state.currentChat) {
      const filteredDocuments = appStateContext.state.uploadedDocuments.filter(document => document.conversationId === appStateContext?.state.currentChat?.id);

      setSelectedUploadedDocuments([]);
      setFilteredUploadedDocuments(filteredDocuments)
    } else {
      setSelectedUploadedDocuments([]);
      setFilteredUploadedDocuments([])
    }
  }, [appStateContext?.state.currentChat, appStateContext?.state.uploadedDocuments])

  const handleFetchUploadedDocuments = async () => {

    if(conversationId) {
      await uploadedDocumentList(offset).then(response => {
        return response
      })
    }

    return []
  }

  useEffect(() => {
    const observer = new IntersectionObserver(
      entries => {
        if (entries[0].isIntersecting) setObserverCounter(observerCounter => (observerCounter += 1))
      },
      { threshold: 1 }
    )

    if (observerTarget.current) observer.observe(observerTarget.current)

    return () => {
      if (observerTarget.current) observer.unobserve(observerTarget.current)
    }
  }, [observerTarget])

  const commandBarButtonStyle: Partial<IStackStyles> = { root: { height: '50px' } }
  React.useEffect(() => {}, [appStateContext?.state.uploadedDocuments])
  
  const onSelectUploadDocument = (itemId: string, isChecked: boolean) => {
    setSelectedUploadedDocuments(prev =>
      isChecked ? [...prev, itemId] : prev.filter(id => id !== itemId)
    );

    handleSelectedUploadDocument(itemId, isChecked);
  };

  return (
    <section className={styles.container} data-is-scrollable aria-label={'document upload panel'}>
      <Stack horizontal horizontalAlign="space-between" verticalAlign="center" wrap aria-label="document upload header">
        <StackItem>
          <Text
            role="heading"
            aria-level={2}
            style={{
              alignSelf: 'center',
              fontWeight: '600',
              fontSize: '18px',
              marginRight: 'auto',
              paddingLeft: '20px'
            }}>
            Uploaded Documents
          </Text>
        </StackItem>
        <Stack verticalAlign="start">
          <Stack horizontal styles={commandBarButtonStyle}>
            <CommandBarButton
              iconProps={{ iconName: 'Cancel' }}
              title={'Hide'}
              onClick={handleDocumentUploadClick}
              aria-label={'hide button'}
              styles={commandBarStyle}
              role="button"
            />
          </Stack>
        </Stack>
      </Stack>
      <Stack
        aria-label="uploaded documents panel content"
        styles={{
          root: {
            display: 'flex',
            flexGrow: 1,
            flexDirection: 'column',
            paddingTop: '2.5px',
            maxWidth: '100%'
          }
        }}
        style={{
          display: 'flex',
          flexGrow: 1,
          flexDirection: 'column',
          flexWrap: 'wrap',
          padding: '1px'
        }}>
        <Stack className={styles.uploadedDocumentListContainer}>
          {appStateContext?.state.uploadedDocumentsLoadingState === UploadedDocumentLoadingState.Success &&
            appStateContext?.state.isCosmosDBAvailable.cosmosDB && <div>{filteredUploadedDocuments.map((item) => {
              return (
                <DocumentListItem item={item} isSelected={selectedUploadedDocuments.includes(item.id)} onSelect={onSelectUploadDocument} />
              )}
            )}</div>}
          {appStateContext?.state.uploadedDocumentsLoadingState === UploadedDocumentLoadingState.Fail &&
            appStateContext?.state.isCosmosDBAvailable && (
              <>
                <Stack>
                  <Stack horizontalAlign="center" verticalAlign="center" style={{ width: '100%', marginTop: 10 }}>
                    <StackItem>
                      <Text style={{ alignSelf: 'center', fontWeight: '400', fontSize: 16 }}>
                        {appStateContext?.state.isCosmosDBAvailable?.status && (
                          <span>{appStateContext?.state.isCosmosDBAvailable?.status}</span>
                        )}
                        {!appStateContext?.state.isCosmosDBAvailable?.status && <span>Error loading uploaded documents</span>}
                      </Text>
                    </StackItem>
                  </Stack>
                </Stack>
              </>
            )}
          {appStateContext?.state.uploadedDocumentsLoadingState === UploadedDocumentLoadingState.Loading && (
            <>
              <Stack>
                <Stack
                  horizontal
                  horizontalAlign="center"
                  verticalAlign="center"
                  style={{ width: '100%', marginTop: 10 }}>
                  <StackItem style={{ justifyContent: 'center', alignItems: 'center' }}>
                    <Spinner
                      style={{ alignSelf: 'flex-start', height: '100%', marginRight: '5px' }}
                      size={SpinnerSize.medium}
                    />
                  </StackItem>
                  <StackItem>
                    <Text style={{ alignSelf: 'center', fontWeight: '400', fontSize: 14 }}>
                      <span style={{ whiteSpace: 'pre-wrap' }}>Loading uploaded documents</span>
                    </Text>
                  </StackItem>
                </Stack>
              </Stack>
            </>
          )}
        </Stack>
      </Stack>
    </section>
  );
}
