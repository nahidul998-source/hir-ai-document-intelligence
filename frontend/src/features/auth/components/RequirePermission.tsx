import React from 'react';
import { useAuthStore } from '../../../stores/authStore';

interface RequirePermissionProps {
    permission: string;
    children: React.ReactNode;
    fallback?: React.ReactNode;
}

export const RequirePermission: React.FC<RequirePermissionProps> = ({ 
    permission, 
    children, 
    fallback = null 
}) => {
    const { permissions } = useAuthStore((state: any) => ({
        permissions: state.permissions || []
    }));

    if (!permissions.includes(permission)) {
        return <>{fallback}</>;
    }

    return <>{children}</>;
};
