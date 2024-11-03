import React, { useContext, useEffect, useRef, useState } from 'react'
import {
  CommandBarButton,
  ContextualMenu,
  DefaultButton,
  Dialog,
  DialogFooter,
  DialogType,
  ICommandBarStyles,
  IContextualMenuItem,
  IStackStyles,
  PrimaryButton,
  Spinner,
  SpinnerSize,
  Stack,
  StackItem,
  Text,
  Checkbox
} from '@fluentui/react'
import { useBoolean } from '@fluentui/react-hooks'

import { historyDeleteAll, uploadedDocumentList, UploadedDocumentLoadingState } from '../../api'
import { AppStateContext } from '../../state/AppProvider'
import styles from './DocumentListPanel.module.css'

interface Props {
  handleSelectedUploadDocument: (id: string, checked:boolean) => void
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

export const DocumentListPanel: React.FC<Props> = ({handleSelectedUploadDocument}) => {
  const appStateContext = useContext(AppStateContext)
  const [showContextualMenu, setShowContextualMenu] = React.useState(false)
  const [hideClearAllDialog, { toggle: toggleClearAllDialog }] = useBoolean(true)
  const [clearing, setClearing] = React.useState(false)
  const [clearingError, setClearingError] = React.useState(false)
  const [offset, setOffset] = useState<number>(25)
  const [observerCounter, setObserverCounter] = useState(0)
  const observerTarget = useRef(null)
  const firstRender = useRef(true)

  const clearAllDialogContentProps = {
    type: DialogType.close,
    title: !clearingError ? 'Are you sure you want to clear all uploaded documents?' : 'Error deleting all uploaded documents',
    closeButtonAriaLabel: 'Close',
    subText: !clearingError
      ? 'All uploaded documents will be permanently removed.'
      : 'Please try again. If the problem persists, please contact the site administrator.'
  }

  const modalProps = {
    titleAriaId: 'labelId',
    subtitleAriaId: 'subTextId',
    isBlocking: true,
    styles: { main: { maxWidth: 450 } }
  }

  const menuItems: IContextualMenuItem[] = [
    { key: 'clearAll', text: 'Clear all uploaded documents', iconProps: { iconName: 'Delete' } }
  ]

  const handleDocumentUploadClick = () => {
    appStateContext?.dispatch({ type: 'TOGGLE_DOCUMENT_LIST' })
  }

  const onShowContextualMenu = React.useCallback((ev: React.MouseEvent<HTMLElement>) => {
    ev.preventDefault() // don't navigate
    setShowContextualMenu(true)
  }, [])

  const onHideContextualMenu = React.useCallback(() => setShowContextualMenu(false), [])

  const onClearAllChatHistory = async () => {
    setClearing(true)
    const response = await historyDeleteAll()
    if (!response.ok) {
      setClearingError(true)
    } else {
      appStateContext?.dispatch({ type: 'DELETE_CHAT_HISTORY' })
      toggleClearAllDialog()
    }
    setClearing(false)
  }

  const onHideClearAllDialog = () => {
    toggleClearAllDialog()
    setTimeout(() => {
      setClearingError(false)
    }, 2000)
  }

  useEffect(() => {
    if (firstRender.current) {
      handleFetchUploadedDocuments()
      firstRender.current = false
      return
    }
    handleFetchUploadedDocuments()
    setOffset(offset => (offset += 25))
  }, [observerCounter])

  const handleFetchUploadedDocuments = async () => {
    await uploadedDocumentList(offset).then(response => {
      console.log(appStateContext?.state.uploadedDocuments)
      return response
    })
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
  React.useEffect(() => {}, [appStateContext?.state.uploadedDocuments, clearingError])
  
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
              iconProps={{ iconName: 'More' }}
              title={'Clear all documents'}
              onClick={onShowContextualMenu}
              aria-label={'clear all documents'}
              styles={commandBarStyle}
              role="button"
              id="moreButton"
            />
            <ContextualMenu
              items={menuItems}
              hidden={!showContextualMenu}
              target={'#moreButton'}
              onItemClick={toggleClearAllDialog}
              onDismiss={onHideContextualMenu}
            />
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
        <Stack className={styles.chatHistoryListContainer}>
          {appStateContext?.state.uploadedDocumentsLoadingState === UploadedDocumentLoadingState.Success &&
            appStateContext?.state.isCosmosDBAvailable.cosmosDB && <div>{appStateContext?.state.uploadedDocuments?.map((item) => {
              return (
                <Stack horizontal key={item.id.toString()} tokens={{ childrenGap: 10 }}>
                  <Checkbox
                    onChange={(e, checked) => handleSelectedUploadDocument(item.id.toString(), checked || false)}
                  />
                  <span>{item.id}</span>
                </Stack>
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
      <Dialog
        hidden={hideClearAllDialog}
        onDismiss={clearing ? () => {} : onHideClearAllDialog}
        dialogContentProps={clearAllDialogContentProps}
        modalProps={modalProps}>
        <DialogFooter>
          {!clearingError && <PrimaryButton onClick={onClearAllChatHistory} disabled={clearing} text="Clear All" />}
          <DefaultButton
            onClick={onHideClearAllDialog}
            disabled={clearing}
            text={!clearingError ? 'Cancel' : 'Close'}
          />
        </DialogFooter>
      </Dialog>
    </section>
  );
}
