import React, { ReactNode } from 'react';
import { Modal, FontWeights, IconButton, getTheme, mergeStyleSets, IIconProps } from '@fluentui/react';
import { IButtonStyles } from '@fluentui/react/lib/Button';

const theme = getTheme();
const iconButtonStyles: Partial<IButtonStyles> = {
  root: {
    color: theme.palette.neutralPrimary,
    marginLeft: 'auto',
    marginTop: '4px',
    marginRight: '2px',
  },
  rootHovered: {
    color: theme.palette.neutralDark,
  },
};

const contentStyles = mergeStyleSets({
    container: {
        minWidth:  '700px',
        minHeight: '500px',
        background: '#f2f2f2',
        borderRadius: '8px'
    },
    header: [
        theme.fonts.xLargePlus,
        {
        flex: '1 1 auto',
        color: theme.palette.neutralPrimary,
        display: 'flex',
        alignItems: 'center',
        fontWeight: FontWeights.semibold,
        padding: '12px 12px 14px 24px',
        },
    ],
    headerBar: {
        position: 'absolute',
        width: '100%',
        height: '4px',
        left: '0%',
        top: '0%',
        background: 'radial-gradient(106.04% 106.06% at 100.1% 90.19%, #0f6cbd 33.63%, #8dddd8 100%)',
        borderTopLeftRadius: '8px',
        borderTopRightRadius: '8px',
    },
    heading: {
        color: theme.palette.neutralPrimary,
        fontWeight: FontWeights.semibold,
        fontSize: 'inherit',
        margin: '0',
    },
    body: {
        flex: '4 4 auto',
        padding: '0 24px 24px 24px',
        overflowY: 'hidden',
        selectors: {
        p: { margin: '14px 0' },
        'p:first-child': { marginTop: 0 },
        'p:last-child': { marginBottom: 0 },
        },
    },
    boxContainer: {
        width: '100%'
    }
});

const cancelIcon: IIconProps = { iconName: 'Cancel' };

interface Props {
    isOpen: boolean;
    onClose: () => void;
    title: string;
    children: ReactNode;
  }

export const CustomModal: React.FC<Props> = ({ isOpen, onClose, title, children }) => {
  return (
    <Modal
      isOpen={isOpen}
      onDismiss={onClose}
      isBlocking={false}
      containerClassName={contentStyles.container}
    >
      <div className={contentStyles.container}>
        <div className={contentStyles.header}>
          <div className={contentStyles.headerBar}></div>
          <h2 className={contentStyles.heading}>
              {title}
          </h2>
          <IconButton
            iconProps={cancelIcon}
            ariaLabel="Close"
            onClick={onClose}
            styles={iconButtonStyles}
          />
        </div>
        <div className={contentStyles.body}>
          {children}
        </div>
      </div>
    </Modal>
  );
}
