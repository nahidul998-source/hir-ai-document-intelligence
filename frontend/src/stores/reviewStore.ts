import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

interface HighlightBox {
  id: string;
  field_name: string;
  page: number;
  x: number;
  y: number;
  width: number;
  height: number;
}

interface ReviewState {
  activeField: string | null;
  zoomLevel: number;
  rotation: number;
  highlights: HighlightBox[];
  unsavedChanges: boolean;
  
  // Actions
  setActiveField: (fieldName: string | null) => void;
  setZoomLevel: (level: number) => void;
  setRotation: (rotation: number) => void;
  setHighlights: (highlights: HighlightBox[]) => void;
  setUnsavedChanges: (status: boolean) => void;
  
  // Undo/Redo stack handling could be extended here
}

export const useReviewStore = create<ReviewState>()(
  devtools(
    persist(
      (set) => ({
        activeField: null,
        zoomLevel: 1.0,
        rotation: 0,
        highlights: [],
        unsavedChanges: false,
        
        setActiveField: (fieldName) => set({ activeField: fieldName }),
        setZoomLevel: (level) => set({ zoomLevel: Math.max(0.5, Math.min(level, 3.0)) }),
        setRotation: (rotation) => set({ rotation }),
        setHighlights: (highlights) => set({ highlights }),
        setUnsavedChanges: (status) => set({ unsavedChanges: status }),
      }),
      {
        name: 'hir-review-storage',
        partialize: (state) => ({ zoomLevel: state.zoomLevel }), // only persist zoom
      }
    )
  )
);
