<template>
  <div id="edit-debtor" class="white pa-6" :class="{ 'border-error-left': showErrorBar }">
    <v-expand-transition>
      <v-row no-gutters>
        <v-col cols="3">
          <label
            class="add-debtor-header generic-label ml"
            :class="{ 'error-text': invalidSection }"
          >
            <span v-if="activeIndex === -1">Add</span>
            <span v-else>
              <span v-if="registrationFlowType === RegistrationFlowType.AMENDMENT
                        && (!currentDebtor.action || currentDebtor.action !== ActionTypes.ADDED)">
                Amend
              </span>
              <span v-else>Edit</span>
            </span>
            <span v-if="currentIsBusiness"> a Business<br />Debtor</span>
            <span v-else> an Individual<br />Debtor</span>
          </label>
        </v-col>
        <v-col cols="9">
          <v-form
            ref="debtorForm"
            class="debtor-form"
            v-on:submit.prevent="addDebtor"
          >
            <v-row v-if="currentIsBusiness" no-gutters class="pb-4">
              <v-col>
                <label class="generic-label">Business Legal Name</label>
              </v-col>
            </v-row>
            <v-row v-else no-gutters class="pb-4">
              <v-col>
                <label class="generic-label">Person's Legal Name</label>
              </v-col>
            </v-row>
            <v-row v-if="currentIsBusiness" no-gutters>
              <v-col>
                <v-text-field
                  filled
                  id="txt-name-debtor"
                  label="Business Legal Name"
                  v-model="searchValue"
                  @keyup="validateNameField()"
                  :error-messages="
                    errors.businessName.message
                      ? errors.businessName.message
                      : ''
                  "
                  persistent-hint
                  :hide-details="hideDetails"
                />
                <auto-complete
                  :searchValue="autoCompleteSearchValue"
                  :setAutoCompleteIsActive="autoCompleteIsActive"
                  v-click-outside="setCloseAutoComplete"
                  @search-value="setSearchValue"
                  @hide-details="setHideDetails"
                >
                </auto-complete>
              </v-col>
            </v-row>
            <v-row v-else no-gutters>
              <v-col cols="4" class="pr-4">
                <v-text-field
                  filled
                  label="First Name"
                  id="txt-first-debtor"
                  v-model="currentDebtor.personName.first"
                  @keyup="validateNameField()"
                  persistent-hint
                  :error-messages="
                    errors.first.message ? errors.first.message : ''
                  "
                />
              </v-col>
              <v-col cols="4" class="pr-4">
                <v-text-field
                  filled
                  label="Middle Name"
                  id="txt-middle-debtor"
                  hint="Required if person has middle name"
                  @keyup="validateNameField()"
                  v-model="currentDebtor.personName.middle"
                  persistent-hint
                  :error-messages="
                    errors.middle.message ? errors.middle.message : ''
                  "
                />
              </v-col>
              <v-col cols="4">
                <v-text-field
                  filled
                  label="Last Name"
                  id="txt-last-debtor"
                  v-model="currentDebtor.personName.last"
                  @keyup="validateNameField()"
                  persistent-hint
                  :error-messages="
                    errors.last.message ? errors.last.message : ''
                  "
                />
              </v-col>
            </v-row>
            <v-row v-if="!currentIsBusiness" class="pb-4" no-gutters>
              <v-col>
                <label class="generic-label">Birthdate</label> (Optional)
              </v-col>
            </v-row>
            <v-row v-if="!currentIsBusiness" no-gutters>
              <v-col cols="4" class="pr-4">
                <v-autocomplete
                  auto-select-first
                  :items="months"
                  filled
                  clearable
                  label="Month"
                  id="txt-month"
                  v-model="month"
                  :error-messages="
                    errors.month.message ? errors.month.message : ''
                  "
                  @keyup="validateBirthdateIfAlreadyValidated"
                  @blur="validateBirthdateIfAlreadyValidated"
                  persistent-hint
                  return-object
                ></v-autocomplete>
              </v-col>
              <v-col cols="4" class="pr-4">
                <v-text-field
                  filled
                  label="Day"
                  id="txt-day"
                  v-model="day"
                  @keyup="validateBirthdateIfAlreadyValidated"
                  :error-messages="errors.day.message ? errors.day.message : ''"
                  persistent-hint
                />
              </v-col>
              <v-col cols="4">
                <v-text-field
                  filled
                  label="Year"
                  id="txt-year"
                  v-model="year"
                  @keyup="validateBirthdateIfAlreadyValidated"
                  :error-messages="
                    errors.year.message ? errors.year.message : ''
                  "
                  persistent-hint
                />
              </v-col>
            </v-row>
            <v-row no-gutters class="pb-4">
              <v-col>
                <label class="generic-label">Email Address</label>
              </v-col>
            </v-row>
            <v-row no-gutters>
              <v-col>
                <v-text-field
                  filled
                  id="txt-email-debtor"
                  label="Email Address (Optional)"
                  v-model="currentDebtor.emailAddress"
                  :error-messages="
                    errors.emailAddress.message
                      ? errors.emailAddress.message
                      : ''
                  "
                  @blur="validateEmail(currentDebtor.emailAddress)"
                  persistent-hint
                />
              </v-col>
            </v-row>
            <v-row no-gutters class="pb-4">
              <v-col>
                <label class="generic-label">Address</label>
              </v-col>
            </v-row>
            <base-address
              ref="regMailingAddress"
              id="address-debtor"
              v-model="currentDebtor.address"
              :editing="true"
              :schema="{ ...addressSchema }"
              :triggerErrors="showAllAddressErrors"
              @valid="updateValidity($event)"
            />

            <v-row>
              <v-col>
                <div class="form__row form__btns">
                  <v-btn
                    large
                    outlined
                    color="error"
                    :disabled="activeIndex === -1"
                    @click="removeDebtor()"
                    id="remove-btn-debtor"
                    class="remove-btn"
                    >
                    <span v-if="registrationFlowType === RegistrationFlowType.AMENDMENT
                              && currentIndex !== -1
                              && (!currentDebtor.action || currentDebtor.action !== ActionTypes.ADDED)">
                      Delete
                    </span>
                    <span v-else>Remove</span>
                  </v-btn>

                  <v-btn
                    large
                    id="done-btn-debtor"
                    class="ml-auto"
                    color="primary"
                    @click="onSubmitForm()"
                  >
                    Done
                  </v-btn>

                  <v-btn
                    id="cancel-btn-debtor"
                    large
                    outlined
                    color="primary"
                    @click="resetFormAndData(true)"
                  >
                    Cancel
                  </v-btn>
                </div>
              </v-col>
            </v-row>
          </v-form>
        </v-col>
      </v-row>
    </v-expand-transition>
  </div>
</template>

<script lang="ts">
// external libraries
import {
  defineComponent,
  onMounted,
  watch,
  computed,
  reactive,
  toRefs
} from '@vue/composition-api'
// local components
import { AutoComplete } from '@/components/search'
import { BaseAddress } from '@/composables/address'
// local helpers / types / etc.
import { useDebtor } from '@/components/parties/composables/useDebtor'
import { useDebtorValidation } from '@/components/parties/composables/useDebtorValidation'
import { formatAddress } from '@/composables/address/factories'
import { useValidation } from '@/utils/validators/use-validation'

export default defineComponent({
  components: {
    BaseAddress,
    AutoComplete
  },
  props: {
    activeIndex: {
      type: Number,
      default: -1
    },
    isBusiness: {
      type: Boolean,
      default: true
    },
    invalidSection: {
      type: Boolean,
      default: false
    },
    setShowErrorBar: {
      type: Boolean,
      default: false
    }
  },
  emits: ['addEditDebtor', 'resetEvent'],
  setup (props, context) {
    const {
      currentDebtor,
      year,
      day,
      monthValue,
      months,
      currentIsBusiness,
      getDebtor,
      getMonthObject,
      resetFormAndData,
      removeDebtor,
      addDebtor,
      addressSchema,
      RegistrationFlowType,
      registrationFlowType,
      ActionTypes
    } = useDebtor(props, context)

    const {
      errors,
      updateValidity,
      validateDebtorForm,
      validateBirthdate,
      validateEmail
    } = useDebtorValidation()

    const {
      validateFirstName,
      validateMiddleName,
      validateLastName,
      validateBusinessName
    } = useValidation()

    const localState = reactive({
      autoCompleteIsActive: true,
      autoCompleteSearchValue: '',
      searchValue: '',
      hideDetails: false,
      month: { value: 0, text: '' },
      showAllAddressErrors: false,
      currentIndex: computed((): number => {
        return props.activeIndex
      }),
      showErrorBar: computed((): boolean => {
        return props.setShowErrorBar
      })
    })

    const onSubmitForm = async () => {
      currentDebtor.value.address = formatAddress(currentDebtor.value.address)
      if (
        validateDebtorForm(
          currentIsBusiness,
          currentDebtor,
          year,
          monthValue,
          day
        ) === true
      ) {
        addDebtor()
      } else {
        // trigger show validation
        localState.showAllAddressErrors = !localState.showAllAddressErrors
      }
    }

    const validateNameField = () => {
      if (!errors.value.first.succeeded || currentDebtor.value.personName.first.length > 50) {
        validateFirstName(currentDebtor.value, errors.value)
      }
      if (!errors.value.last.succeeded || currentDebtor.value.personName.last.length > 50) {
        validateLastName(currentDebtor.value, errors.value)
      }
      if (!errors.value.middle.succeeded || currentDebtor.value.personName.middle.length > 50) {
        validateMiddleName(currentDebtor.value, errors.value)
      }
      if (!errors.value.businessName.succeeded || currentDebtor.value.businessName.length > 150) {
        validateBusinessName(currentDebtor.value, errors.value)
      }
    }

    const validateBirthdateIfAlreadyValidated = () => {
      if (
        !errors.value.year.succeeded ||
        !errors.value.month.succeeded ||
        !errors.value.day.succeeded
      ) {
        validateBirthdate(year.value, monthValue.value, day.value)
      }
    }

    const setSearchValue = (searchValueTyped: string) => {
      localState.autoCompleteIsActive = false
      localState.searchValue = searchValueTyped
      currentDebtor.value.businessName = searchValueTyped
    }

    const setHideDetails = (hideDetails: boolean) => {
      localState.hideDetails = hideDetails
    }

    const setCloseAutoComplete = () => {
      localState.autoCompleteIsActive = false
    }

    onMounted(() => {
      getDebtor()
      setSearchValue(currentDebtor.value.businessName)
      localState.month = getMonthObject()
    })

    watch(
      () => localState.searchValue,
      (val: string) => {
        localState.autoCompleteSearchValue = val
        // only open if debtor name changed
        if (currentDebtor.value.businessName !== val) {
          // show autocomplete results when there is a searchValue
          localState.autoCompleteIsActive = val !== ''
          currentDebtor.value.businessName = val
        }
      }
    )

    watch(
      () => localState.month,
      currentValue => {
        if (currentValue) {
          monthValue.value = currentValue.value
        } else {
          monthValue.value = 0
        }
      }
    )

    return {
      currentDebtor,
      year,
      day,
      months,
      currentIsBusiness,
      resetFormAndData,
      removeDebtor,
      onSubmitForm,
      validateBirthdateIfAlreadyValidated,
      setSearchValue,
      setHideDetails,
      setCloseAutoComplete,
      addressSchema,
      updateValidity,
      validateEmail,
      validateNameField,
      errors,
      RegistrationFlowType,
      registrationFlowType,
      ActionTypes,
      ...toRefs(localState)
    }
  }
})
</script>

<style lang="scss" module>
@import '@/assets/styles/theme.scss';
</style>
