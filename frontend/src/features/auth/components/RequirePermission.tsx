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
    // In a real app, useAuthStore would contain the user's permissions array
    const { permissions } = useAuthStore((state: any) => ({
        permissions: state.permissions || ['review:write', 'review:approve', 'review:read'] // Mock default permissions
    }));

    if (!permissions.includes(permission)) {
        return <>{fallback}</>;
    }

    return <>{children}</>;
};
