from django.urls import path
from . import views
from messaging import views as msg_views

urlpatterns = [
    path("login/", views.bo_login, name="bo_login"),
    path("logout/", views.bo_logout, name="bo_logout"),
    path("", views.dashboard, name="bo_dashboard"),

    path("produits/", views.products_list, name="bo_products_list"),
    path("produits/nouveau/", views.product_create, name="bo_product_create"),
    path("produits/<int:pk>/modifier/", views.product_edit, name="bo_product_edit"),

    path("depots/", views.deposits_list, name="bo_deposits_list"),
    path("depots/<int:pk>/approuver/", views.deposit_approve, name="bo_deposit_approve"),
    path("depots/<int:pk>/rejeter/", views.deposit_reject, name="bo_deposit_reject"),

    path("retraits/", views.withdrawals_list, name="bo_withdrawals_list"),
    path("retraits/<int:pk>/approuver/", views.withdraw_approve, name="bo_withdraw_approve"),
    path("retraits/<int:pk>/rejeter/", views.withdraw_reject, name="bo_withdraw_reject"),

    path("utilisateurs/", views.users_list, name="bo_users_list"),
    path("utilisateurs/nouveau/", views.user_create, name="bo_user_create"),
    path("utilisateurs/<int:user_id>/modifier/", views.user_edit, name="bo_user_edit"),
    path("utilisateurs/<int:user_id>/mot-de-passe/", views.user_set_password, name="bo_user_set_password"),

    path("wallets/", views.wallets_list, name="bo_wallets_list"),
    path("wallets/<int:user_id>/", views.wallet_detail, name="bo_wallet_detail"),

    path("investissements/", views.investments_list, name="bo_investments_list"),

    # ✅ Messagerie backoffice
    path("messages/", msg_views.bo_inbox, name="bo_messages_list"),
    path("messages/<int:conv_id>/", msg_views.bo_chat, name="bo_messages_chat"),
    path("messages/<int:conv_id>/send/", msg_views.bo_send, name="bo_messages_send"),
]