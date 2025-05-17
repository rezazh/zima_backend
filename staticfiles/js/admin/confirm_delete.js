// فایل static/js/admin/confirm_delete.js
document.addEventListener('DOMContentLoaded', function() {
    // تأیید قبل از حذف محصول
    const deleteLinks = document.querySelectorAll('a.deletelink');
    deleteLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            if (!confirm('آیا از حذف این مورد اطمینان دارید؟ این عمل غیرقابل بازگشت است.')) {
                e.preventDefault();
            }
        });
    });
    
    // تأیید قبل از حذف گروهی
    const actionForm = document.querySelector('#changelist-form');
    if (actionForm) {
        actionForm.addEventListener('submit', function(e) {
            const action = document.querySelector('select[name="action"]').value;
            if (action === 'delete_selected') {
                if (!confirm('آیا از حذف موارد انتخاب شده اطمینان دارید؟ این عمل غیرقابل بازگشت است.')) {
                    e.preventDefault();
                }
            }
        });
    }
});