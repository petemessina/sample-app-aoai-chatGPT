import * as React from 'react'
import { useContext, useEffect, useRef, useState } from 'react'
import { ITextField, Stack, Checkbox, IconButton, Dialog, DialogFooter, PrimaryButton, DefaultButton, DialogType } from '@fluentui/react'
import { UploadedDocument, DocumentPayload } from '../../api/models'
import { AppStateContext } from '../../state/AppProvider'
import { useBoolean } from '@fluentui/react-hooks'

import { documentDelete } from '../../api'
import styles from './DocumentListPanel.module.css'

interface Props {
  item: UploadedDocument,
  isSelected: boolean,
  onSelect: (id: string, checked:boolean) => void  
}

export const DocumentListItem: React.FC<Props> = ({ item, isSelected, onSelect }) => {
    const [textFieldFocused, setTextFieldFocused] = useState(false)
    const [isHovered, setIsHovered] = React.useState(false)
    const [errorDelete, setErrorDelete] = useState(false)
    const [hideDeleteDialog, { toggle: toggleDeleteDialog }] = useBoolean(true)
    const textFieldRef = useRef<ITextField | null>(null)
    const appStateContext = React.useContext(AppStateContext)
    const dialogContentProps = {
        type: DialogType.close,
        title: 'Are you sure you want to delete this item?',
        closeButtonAriaLabel: 'Close',
        subText: 'The uploaded document will be permanently removed.'
      }

    const modalProps = {
        titleAriaId: 'labelId',
        subtitleAriaId: 'subTextId',
        isBlocking: true,
        styles: { main: { maxWidth: 450 } }
    }

    useEffect(() => {
      if (textFieldFocused && textFieldRef.current) {
        textFieldRef.current.focus()
        setTextFieldFocused(false)
      }
    }, [textFieldFocused])
  
    const onDelete = async () => {
        const response = await documentDelete(item.id)

        if (!response.ok) {
          setErrorDelete(true)
          setTimeout(() => { setErrorDelete(false) }, 5000)
        } else {
          appStateContext?.dispatch({ type: 'DELETE_UPLOADED_DOCUMENT', payload: item.id })
        }

        toggleDeleteDialog()
    }
      
    return (
      <Stack
        key={item.id}
        tabIndex={0}
        aria-label="uploaded document item"
        className={styles.itemCell}
        verticalAlign="center"
        onClick={() => onSelect(item.id, !isSelected)}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        styles={{
          root: {
            backgroundColor: isSelected ? '#e6e6e6' : 'transparent'
          }
        }}>
            <Stack horizontal verticalAlign={'center'} style={{ width: '100%' }}>
                <Checkbox checked={isSelected} onChange={(e, checked) => onSelect(item.id, checked || false)} />
                <span>{item.payload?.find(item => item.Key === "file")?.Value}</span>
                {(isSelected || isHovered) && (
                    <Stack horizontal horizontalAlign="end">
                        <IconButton
                            className={styles.itemButton}
                            iconProps={{ iconName: 'Delete' }}
                            title="Delete"
                            onClick={toggleDeleteDialog}
                            onKeyDown={e => (e.key === ' ' ? toggleDeleteDialog() : null)}
                        />
                    </Stack>
                )}
            </Stack>
            <Dialog
                hidden={hideDeleteDialog}
                onDismiss={toggleDeleteDialog}
                dialogContentProps={dialogContentProps}
                modalProps={modalProps}>
                <DialogFooter>
                    <PrimaryButton onClick={onDelete} text="Delete" />
                    <DefaultButton onClick={toggleDeleteDialog} text="Cancel" />
                </DialogFooter>
            </Dialog>
      </Stack>
    )
  }