import "@goauthentik/admin/common/ak-flow-search/ak-source-flow-search";
import { iconHelperText, placeholderHelperText } from "@goauthentik/admin/helperText";
import { BaseSourceForm } from "@goauthentik/admin/sources/BaseSourceForm";
import {
    GroupMatchingModeToLabel,
    UserMatchingModeToLabel,
} from "@goauthentik/admin/sources/oauth/utils";
import { DEFAULT_CONFIG, config } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/components/ak-switch-input";
import "@goauthentik/components/ak-text-input";
import "@goauthentik/components/ak-textarea-input";
import {
    CapabilitiesEnum,
    WithCapabilitiesConfig,
} from "@goauthentik/elements/Interface/capabilitiesProvider";
import "@goauthentik/elements/ak-dual-select/ak-dual-select-dynamic-selected-provider.js";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import "@goauthentik/elements/forms/SearchSelect";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    FlowsInstancesListDesignationEnum,
    TelegramSource,
    TelegramSourceRequest,
    SourcesApi,
} from "@goauthentik/api";

@customElement("ak-source-telegram-form")
export class TelegramSourceForm extends WithCapabilitiesConfig(BaseSourceForm<TelegramSource>) {
    async loadInstance(pk: string): Promise<TelegramSource> {
        const source = await new SourcesApi(DEFAULT_CONFIG).sourcesTelegramRetrieve({
            slug: pk,
        });
        this.clearIcon = false;
        return source;
    }

    @state()
    clearIcon = false;

    async send(data: TelegramSource): Promise<TelegramSource> {
        let source: TelegramSource;
        if (this.instance) {
            source = await new SourcesApi(DEFAULT_CONFIG).sourcesTelegramPartialUpdate({
                slug: this.instance.slug,
                patchedTelegramSourceRequest: data,
            });
        } else {
            source = await new SourcesApi(DEFAULT_CONFIG).sourcesTelegramCreate({
                telegramSourceRequest: data as unknown as TelegramSourceRequest,
            });
        }
        const c = await config();
        if (c.capabilities.includes(CapabilitiesEnum.CanSaveMedia)) {
            const icon = this.getFormFiles()["icon"];
            if (icon || this.clearIcon) {
                await new SourcesApi(DEFAULT_CONFIG).sourcesAllSetIconCreate({
                    slug: source.slug,
                    file: icon,
                    clear: this.clearIcon,
                });
            }
        } else {
            await new SourcesApi(DEFAULT_CONFIG).sourcesAllSetIconUrlCreate({
                slug: source.slug,
                filePathRequest: {
                    url: data.icon || "",
                },
            });
        }
        return source;
    }

    renderForm(): TemplateResult {
        return html` <ak-text-input
                name="name"
                label=${msg("Name")}
                value=${ifDefined(this.instance?.name)}
                required
            ></ak-text-input>
            <ak-text-input
                name="slug"
                label=${msg("Slug")}
                value=${ifDefined(this.instance?.slug)}
                required
            ></ak-text-input>
            <ak-switch-input
                name="enabled"
                ?checked=${first(this.instance?.enabled, true)}
                label=${msg("Enabled")}
            ></ak-switch-input>
            <ak-text-input
                name="botId"
                label=${msg("Bot Id")}
                value=${ifDefined(this.instance?.botId)}
                required
            ></ak-text-input>
            <ak-form-element-horizontal
                label=${msg("Consumer secret")}
                ?required=${true}
                ?writeOnly=${this.instance !== undefined}
                name="botToken"
            >
                <textarea class="pf-c-form-control"></textarea>
            </ak-form-element-horizontal>
            <ak-text-input
                name="userPathTemplate"
                label=${msg("User path")}
                value=${first(
                    this.instance?.userPathTemplate,
                    "goauthentik.io/sources/%(slug)s",
                )}
                help=${placeholderHelperText}
            ></ak-text-input>
            <ak-form-group>
                <span slot="header"> ${msg("Flow settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Authentication flow")}
                        name="authenticationFlow"
                    >
                        <ak-source-flow-search
                            flowType=${FlowsInstancesListDesignationEnum.Authentication}
                            .currentFlow=${this.instance?.authenticationFlow}
                            .instanceId=${this.instance?.pk}
                            fallback="default-source-authentication"
                        ></ak-source-flow-search>
                        <p class="pf-c-form__helper-text">
                            ${msg("Flow to use when authenticating existing users.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Enrollment flow")}
                        name="enrollmentFlow"
                    >
                        <ak-source-flow-search
                            flowType=${FlowsInstancesListDesignationEnum.Enrollment}
                            .currentFlow=${this.instance?.enrollmentFlow}
                            .instanceId=${this.instance?.pk}
                            fallback="default-source-enrollment"
                        ></ak-source-flow-search>
                        <p class="pf-c-form__helper-text">
                            ${msg("Flow to use when enrolling new users.")}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-source-telegram-form": TelegramSourceForm;
    }
}
