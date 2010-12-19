=================
django-model-i18n 
=================

**django-model-i18n is a django application that tries to make multilingual data in models less painful.**

The main features/goals are:

 * Easy installation and integration. No data or schema migration pain.
 * Each multilingual model stores it's translations in a separate table, which from django is just a new model dynamically created, we call this model the translation model.
 * You can add (or even drop) i18n support for a model at any time and you won't need to migrate any data or affect the original model (we call this the master model) table definition. This allows you to develop your apps without thinking in the i18n part (you even can load data for the main language and you won't need to migrate it) and when you are comfortable with it register the multilingual options and start working with the content translations.
 * 3rd party apps friendly. You can add i18n support to the existing models without modifying their definition at all (think in apps you can't modify directly for example djago.contrib.flatpages).
