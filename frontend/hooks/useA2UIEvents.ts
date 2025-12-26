import { useA2UIStore } from '@/stores/a2uiStore';
import type { A2UIMessage } from '@/types/a2ui';

export const useA2UIEvents = () => {
  const {
    createOrUpdateSurface,
    updateDataModel,
    beginRendering,
    deleteSurface
  } = useA2UIStore();
  
  const processA2UIMessage = (message: any, messageId?: string) => {
    // Type guard to check if message is A2UI (not AG-UI)
    if (!message.type) return;
    
    const a2uiMessage = message as A2UIMessage;
    
    switch (a2uiMessage.type) {
      case 'surfaceUpdate':
        console.log('[A2UI] Processing surfaceUpdate:', a2uiMessage);
        createOrUpdateSurface(
          a2uiMessage.surfaceId,
          a2uiMessage.components,
          messageId
        );
        break;
        
      case 'dataModelUpdate':
        console.log('[A2UI] Processing dataModelUpdate:', a2uiMessage);
        updateDataModel(
          a2uiMessage.surfaceId,
          a2uiMessage.path,
          a2uiMessage.contents
        );
        break;
        
      case 'beginRendering':
        console.log('[A2UI] Processing beginRendering:', a2uiMessage);
        beginRendering(
          a2uiMessage.surfaceId,
          a2uiMessage.rootComponentId
        );
        break;
        
      case 'deleteSurface':
        console.log('[A2UI] Processing deleteSurface:', a2uiMessage);
        deleteSurface(a2uiMessage.surfaceId);
        break;
    }
  };
  
  return { processA2UIMessage };
};
