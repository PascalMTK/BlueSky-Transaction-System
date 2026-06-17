from django.urls import path
from core.views import auth_views, admin_views, agent_views, profile_views

urlpatterns = [
    # ── Welcome & Auth ────────────────────────────────────────────────────
    path('',                              auth_views.welcome,       name='welcome'),
    path('login/',                        auth_views.login_view,    name='login'),
    path('logout/',                       auth_views.logout_view,   name='logout'),
    path('register/',                     auth_views.register_view, name='register'),
    path('lang/<str:locale>/',            auth_views.lang_switch,   name='lang_switch'),
    # ── Profile ───────────────────────────────────────────────────────────
    path('profile/',                      profile_views.profile_show,     name='profile_show'),
    path('profile/update/',               profile_views.profile_update,   name='profile_update'),
    path('profile/photo/',                profile_views.profile_photo,    name='profile_photo'),
    path('profile/password/',             profile_views.profile_password, name='profile_password'),

    # ── Admin — Dashboard ─────────────────────────────────────────────────
    path('admin/dashboard/',              admin_views.dashboard,          name='admin_dashboard'),
    path('admin/statistics/',             admin_views.statistics,         name='admin_statistics'),

    # ── Admin — Agents ────────────────────────────────────────────────────
    path('admin/agents/',                 admin_views.agents,             name='admin_agents'),
    path('admin/agents/<int:agent_id>/status/',   admin_views.agent_status,       name='admin_agent_status'),
    path('admin/agents/<int:agent_id>/promote/',  admin_views.agent_promote,      name='admin_agent_promote'),
    path('admin/agents/<int:agent_id>/password/', admin_views.agent_set_password, name='admin_agent_set_password'),
    path('admin/agents/<int:agent_id>/delete/',   admin_views.agent_destroy,      name='admin_agent_destroy'),

    # ── Admin — Transactions ──────────────────────────────────────────────
    path('admin/transactions/',           admin_views.transactions,       name='admin_transactions'),

    # ── Admin — Reports ───────────────────────────────────────────────────
    path('admin/reports/',                admin_views.reports,            name='admin_reports'),
    path('admin/reports/<int:report_id>/read/',  admin_views.report_read,  name='admin_report_read'),
    path('admin/reports/<int:report_id>/reply/', admin_views.report_reply, name='admin_report_reply'),

    # ── Admin — Countries ─────────────────────────────────────────────────
    path('admin/countries/',              admin_views.countries_index,    name='admin_countries'),
    path('admin/countries/create/',       admin_views.countries_create,   name='admin_countries_create'),
    path('admin/countries/<int:country_id>/edit/',   admin_views.countries_edit,    name='admin_countries_edit'),
    path('admin/countries/<int:country_id>/toggle/', admin_views.countries_toggle,  name='admin_countries_toggle'),
    path('admin/countries/<int:country_id>/delete/', admin_views.countries_destroy, name='admin_countries_destroy'),

    # ── Admin — Export & Reset ────────────────────────────────────────────
    path('admin/export/csv/',             admin_views.export_csv,         name='admin_export_csv'),
    path('admin/reset/system/',           admin_views.reset_system,       name='admin_reset_system'),
    path('admin/reset/country/<int:country_id>/', admin_views.reset_by_country, name='admin_reset_country'),

    # ── Agent — Dashboard ─────────────────────────────────────────────────
    path('agent/dashboard/',              agent_views.dashboard,          name='agent_dashboard'),

    # ── Agent — Transactions ──────────────────────────────────────────────
    path('agent/transactions/',           agent_views.tx_index,           name='tx_index'),
    path('agent/transactions/create/',    agent_views.tx_create,          name='tx_create'),
    path('agent/transactions/<int:tx_id>/',        agent_views.tx_show,    name='tx_show'),
    path('agent/transactions/<int:tx_id>/edit/',   agent_views.tx_edit,    name='tx_edit'),
    path('agent/transactions/<int:tx_id>/print/',  agent_views.tx_print,   name='tx_print'),
    path('agent/transactions/<int:tx_id>/delete/', agent_views.tx_destroy, name='tx_destroy'),

    # ── Agent — Network transactions (read-only, all countries) ───────────
    path('network/',                      agent_views.tx_network,             name='tx_network'),

    # ── Direct messaging ──────────────────────────────────────────────────
    path('messages/',                        agent_views.messages_list,     name='messages_list'),
    path('messages/<int:user_id>/',          agent_views.messages_thread,   name='messages_thread'),
    path('messages/delete/<int:msg_id>/',    agent_views.message_delete,    name='message_delete'),
    path('messages/<int:user_id>/delete/',   agent_views.conversation_delete, name='conversation_delete'),
    path('messages/<int:user_id>/since/<int:since_id>/', agent_views.messages_since, name='messages_since'),

    # ── Agent — Reports & Export ──────────────────────────────────────────
    path('agent/reports/',                    agent_views.report_store,         name='agent_report_store'),
    path('agent/reports/portal/',             agent_views.agent_reports_portal, name='agent_reports_portal'),
    path('agent/reports/<int:report_id>/delete/', agent_views.report_delete,   name='report_delete'),
    path('agent/export/csv/',             agent_views.export_csv,         name='agent_export_csv'),

    # ── API ───────────────────────────────────────────────────────────────
    path('api/countries/<int:country_id>/fee/', agent_views.fee_for_country, name='api_country_fee'),
]
