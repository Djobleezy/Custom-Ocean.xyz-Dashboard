"use strict";

// Global variables
let currentFilter = "all";
let currentOffset = 0;
const pageSize = 20;
let hasMoreNotifications = true;
let isLoading = false;

// Initialize when document is ready
$(document).ready(() => {
    console.log("Notification page initializing...");

    // Set up filter buttons
    $('.filter-button').click(function () {
        $('.filter-button').removeClass('active');
        $(this).addClass('active');
        currentFilter = $(this).data('filter');
        resetAndLoadNotifications();
    });

    // Set up action buttons
    $('#mark-all-read').click(markAllAsRead);
    $('#clear-read').click(clearReadNotifications);
    $('#clear-all').click(clearAllNotifications);
    $('#load-more').click(loadMoreNotifications);

    // Initial load of notifications
    loadNotifications();

    // Start polling for unread count
    startUnreadCountPolling();

    // Initialize BitcoinMinuteRefresh if available
    if (typeof BitcoinMinuteRefresh !== 'undefined' && BitcoinMinuteRefresh.initialize) {
        BitcoinMinuteRefresh.initialize(refreshNotifications);
        console.log("BitcoinMinuteRefresh initialized with refresh function");
    }

    // Start periodic update of notification timestamps every 30 seconds
    setInterval(updateNotificationTimestamps, 30000);
});

// Load notifications with current filter
function loadNotifications() {
    if (isLoading) return;

    isLoading = true;
    showLoading();

    const params = {
        limit: pageSize,
        offset: currentOffset
    };

    if (currentFilter !== "all") {
        params.category = currentFilter;
    }

    $.ajax({
        url: `/api/notifications?${$.param(params)}`,
        method: "GET",
        dataType: "json",
        success: (data) => {
            renderNotifications(data.notifications, currentOffset === 0);
            updateUnreadBadge(data.unread_count);

            // Update load more button state
            hasMoreNotifications = data.notifications.length === pageSize;
            $('#load-more').prop('disabled', !hasMoreNotifications);

            isLoading = false;
        },
        error: (xhr, status, error) => {
            console.error("Error loading notifications:", error);
            showError("Failed to load notifications. Please try again.");
            isLoading = false;
        }
    });
}

// Reset offset and load notifications
function resetAndLoadNotifications() {
    currentOffset = 0;
    loadNotifications();
}

// Load more notifications
function loadMoreNotifications() {
    if (!hasMoreNotifications || isLoading) return;

    currentOffset += pageSize;
    loadNotifications();
}

// Refresh notifications (for periodic updates)
function refreshNotifications() {
    // Only refresh if we're on the first page
    if (currentOffset === 0) {
        resetAndLoadNotifications();
    } else {
        // Just update the unread count
        updateUnreadCount();
    }
}

// Update notification timestamps to relative time
function updateNotificationTimestamps() {
    $('.notification-item').each(function () {
        const timestampStr = $(this).attr('data-timestamp');
        if (timestampStr) {
            const timestamp = new Date(timestampStr);
            const relativeTime = formatTimestamp(timestamp);
            $(this).find('.notification-time').text(relativeTime);
        }
    });
}

// Show loading indicator
function showLoading() {
    if (currentOffset === 0) {
        // First page load, show loading message
        $('#notifications-container').html('<div class="loading-message">Loading notifications<span class="terminal-cursor"></span></div>');
    } else {
        // Pagination load, show loading below
        $('#load-more').prop('disabled', true).text('Loading...');
    }
}

// Show error message
function showError(message) {
    $('#notifications-container').html(`<div class="error-message">${message}</div>`);
    $('#load-more').hide();
}

// Render notifications in the container
function renderNotifications(notifications, isFirstPage) {
    const container = $('#notifications-container');

    // If first page and no notifications
    if (isFirstPage && (!notifications || notifications.length === 0)) {
        container.html($('#empty-template').html());
        $('#load-more').hide();
        return;
    }

    // If first page, clear container
    if (isFirstPage) {
        container.empty();
    }

    // Render each notification
    notifications.forEach(notification => {
        const notificationElement = createNotificationElement(notification);
        container.append(notificationElement);
    });

    // Show/hide load more button
    $('#load-more').show().prop('disabled', !hasMoreNotifications);
}

// Create notification element from template
function createNotificationElement(notification) {
    const template = $('#notification-template').html();
    const element = $(template);

    // Set data attributes
    element.attr('data-id', notification.id)
        .attr('data-level', notification.level)
        .attr('data-category', notification.category)
        .attr('data-read', notification.read)
        .attr('data-timestamp', notification.timestamp);

    // Set icon based on level
    const iconElement = element.find('.notification-icon i');
    switch (notification.level) {
        case 'success':
            iconElement.addClass('fa-check-circle');
            break;
        case 'info':
            iconElement.addClass('fa-info-circle');
            break;
        case 'warning':
            iconElement.addClass('fa-exclamation-triangle');
            break;
        case 'error':
            iconElement.addClass('fa-times-circle');
            break;
        default:
            iconElement.addClass('fa-bell');
    }

    // Append "Z" to indicate UTC if not present
    let utcTimestampStr = notification.timestamp;
    if (!utcTimestampStr.endsWith('Z')) {
        utcTimestampStr += 'Z';
    }
    const utcDate = new Date(utcTimestampStr);

    // Convert UTC date to Los Angeles time with a timezone name for clarity
    const fullTimestamp = utcDate.toLocaleString('en-US', {
        timeZone: 'America/Los_Angeles',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        timeZoneName: 'short'
    });

    // Append the full timestamp to the notification message
    const messageWithTimestamp = `${notification.message}<br><span class="full-timestamp">${fullTimestamp}</span>`;
    element.find('.notification-message').html(messageWithTimestamp);

    // Set metadata for relative time display
    element.find('.notification-time').text(formatTimestamp(utcDate));
    element.find('.notification-category').text(notification.category);

    // Set up action buttons
    element.find('.mark-read-button').on('click', (e) => {
        e.stopPropagation();
        markAsRead(notification.id);
    });
    element.find('.delete-button').on('click', (e) => {
        e.stopPropagation();
        deleteNotification(notification.id);
    });

    // Hide mark as read button if already read
    if (notification.read) {
        element.find('.mark-read-button').hide();
    }

    return element;
}

// Format timestamp as relative time
function formatTimestamp(timestamp) {
    const now = new Date();
    const diffMs = now - timestamp;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);

    if (diffSec < 60) {
        return "just now";
    } else if (diffMin < 60) {
        return `${diffMin}m ago`;
    } else if (diffHour < 24) {
        return `${diffHour}h ago`;
    } else if (diffDay < 30) {
        return `${diffDay}d ago`;
    } else {
        // Format as date for older notifications
        return timestamp.toLocaleDateString('en-US', { timeZone: 'America/Los_Angeles' });
    }
}

// Mark a notification as read
function markAsRead(notificationId) {
    $.ajax({
        url: "/api/notifications/mark_read",
        method: "POST",
        data: JSON.stringify({ notification_id: notificationId }),
        contentType: "application/json",
        success: (data) => {
            // Update UI
            $(`[data-id="${notificationId}"]`).attr('data-read', 'true');
            $(`[data-id="${notificationId}"]`).find('.mark-read-button').hide();

            // Update unread badge
            updateUnreadBadge(data.unread_count);
        },
        error: (xhr, status, error) => {
            console.error("Error marking notification as read:", error);
        }
    });
}

// Mark all notifications as read
function markAllAsRead() {
    $.ajax({
        url: "/api/notifications/mark_read",
        method: "POST",
        data: JSON.stringify({}),
        contentType: "application/json",
        success: (data) => {
            // Update UI
            $('.notification-item').attr('data-read', 'true');
            $('.mark-read-button').hide();

            // Update unread badge
            updateUnreadBadge(0);
        },
        error: (xhr, status, error) => {
            console.error("Error marking all notifications as read:", error);
        }
    });
}

// Delete a notification
function deleteNotification(notificationId) {
    $.ajax({
        url: "/api/notifications/delete",
        method: "POST",
        data: JSON.stringify({ notification_id: notificationId }),
        contentType: "application/json",
        success: (data) => {
            // Remove from UI with animation
            $(`[data-id="${notificationId}"]`).fadeOut(300, function () {
                $(this).remove();

                // Check if container is empty now
                if ($('#notifications-container').children().length === 0) {
                    $('#notifications-container').html($('#empty-template').html());
                    $('#load-more').hide();
                }
            });

            // Update unread badge
            updateUnreadBadge(data.unread_count);
        },
        error: (xhr, status, error) => {
            console.error("Error deleting notification:", error);
        }
    });
}

// Clear read notifications
function clearReadNotifications() {
    if (!confirm("Are you sure you want to clear all read notifications?")) {
        return;
    }

    $.ajax({
        url: "/api/notifications/clear",
        method: "POST",
        data: JSON.stringify({
            // Special parameter to clear only read notifications
            read_only: true
        }),
        contentType: "application/json",
        success: () => {
            // Reload notifications
            resetAndLoadNotifications();
        },
        error: (xhr, status, error) => {
            console.error("Error clearing read notifications:", error);
        }
    });
}

// Clear all notifications
function clearAllNotifications() {
    if (!confirm("Are you sure you want to clear ALL notifications? This cannot be undone.")) {
        return;
    }

    $.ajax({
        url: "/api/notifications/clear",
        method: "POST",
        data: JSON.stringify({}),
        contentType: "application/json",
        success: () => {
            // Reload notifications
            resetAndLoadNotifications();
        },
        error: (xhr, status, error) => {
            console.error("Error clearing all notifications:", error);
        }
    });
}

// Update unread badge
function updateUnreadBadge(count) {
    $('#unread-badge').text(count);

    // Add special styling if unread
    if (count > 0) {
        $('#unread-badge').addClass('has-unread');
    } else {
        $('#unread-badge').removeClass('has-unread');
    }
}

// Update unread count from API
function updateUnreadCount() {
    $.ajax({
        url: "/api/notifications/unread_count",
        method: "GET",
        success: (data) => {
            updateUnreadBadge(data.unread_count);
        },
        error: (xhr, status, error) => {
            console.error("Error updating unread count:", error);
        }
    });
}

// Start polling for unread count
function startUnreadCountPolling() {
    // Update every 30 seconds
    setInterval(updateUnreadCount, 30000);
}
