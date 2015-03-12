import os
import time
import csv
import ConfigParser
import random

from django.contrib.auth.models import User
from django.core.management.base import NoArgsCommand, CommandError

MALE_FIRST_NAMES = ['JAMES', 'JOHN', 'ROBERT', 'MICHAEL', 'WILLIAM', 'DAVID', 'RICHARD', 'CHARLES', 'JOSEPH', 'THOMAS', 'CHRISTOPHER', 'DANIEL', 'PAUL', 'MARK', 'DONALD', 'GEORGE', 'KENNETH', 'STEVEN', 'EDWARD', 'BRIAN', 'RONALD', 'ANTHONY', 'KEVIN', 'JASON', 'MATTHEW', 'GARY', 'TIMOTHY', 'JOSE', 'LARRY', 'JEFFREY', 'FRANK', 'SCOTT', 'ERIC', 'STEPHEN', 'ANDREW', 'RAYMOND', 'GREGORY', 'JOSHUA', 'JERRY', 'DENNIS', 'WALTER', 'PATRICK', 'PETER', 'HAROLD', 'DOUGLAS', 'HENRY', 'CARL', 'ARTHUR', 'RYAN', 'ROGER', 'JOE', 'JUAN', 'JACK', 'ALBERT', 'JONATHAN', 'JUSTIN', 'TERRY', 'GERALD', 'KEITH', 'SAMUEL', 'WILLIE', 'RALPH', 'LAWRENCE', 'NICHOLAS', 'ROY', 'BENJAMIN', 'BRUCE', 'BRANDON', 'ADAM', 'HARRY', 'FRED', 'WAYNE', 'BILLY', 'STEVE', 'LOUIS', 'JEREMY', 'AARON', 'RANDY', 'HOWARD', 'EUGENE', 'CARLOS', 'RUSSELL', 'BOBBY', 'VICTOR', 'MARTIN', 'ERNEST', 'PHILLIP', 'TODD', 'JESSE', 'CRAIG', 'ALAN', 'SHAWN', 'CLARENCE', 'SEAN', 'PHILIP']
FEMALE_FIRST_NAMES = ['MARY', 'PATRICIA', 'LINDA', 'BARBARA', 'ELIZABETH', 'JENNIFER', 'MARIA', 'SUSAN', 'MARGARET', 'DOROTHY', 'LISA', 'NANCY', 'KAREN', 'BETTY', 'HELEN', 'SANDRA', 'DONNA', 'CAROL', 'RUTH', 'SHARON', 'MICHELLE', 'LAURA', 'SARAH', 'KIMBERLY', 'DEBORAH', 'JESSICA', 'SHIRLEY', 'CYNTHIA', 'ANGELA', 'MELISSA', 'BRENDA', 'AMY', 'ANNA', 'REBECCA', 'VIRGINIA', 'KATHLEEN', 'PAMELA', 'MARTHA', 'DEBRA', 'AMANDA', 'STEPHANIE', 'CAROLYN', 'CHRISTINE', 'MARIE', 'JANET', 'CATHERINE', 'FRANCES', 'ANN', 'JOYCE', 'DIANE', 'ALICE', 'JULIE', 'HEATHER', 'TERESA', 'DORIS', 'GLORIA', 'EVELYN', 'JEAN', 'CHERYL', 'MILDRED', 'KATHERINE', 'JOAN', 'ASHLEY', 'JUDITH', 'ROSE', 'JANICE', 'KELLY', 'NICOLE', 'JUDY', 'CHRISTINA', 'KATHY', 'THERESA', 'BEVERLY', 'DENISE', 'TAMMY', 'IRENE', 'JANE', 'LORI', 'RACHEL', 'MARILYN', 'ANDREA', 'KATHRYN', 'LOUISE', 'SARA', 'ANNE', 'JACQUELINE', 'WANDA', 'BONNIE', 'JULIA', 'RUBY', 'LOIS', 'TINA']
LAST_NAMES = ['SMITH', 'JOHNSON', 'WILLIAMS', 'BROWN', 'JONES', 'MILLER', 'DAVIS', 'GARCIA', 'RODRIGUEZ', 'WILSON', 'MARTINEZ', 'ANDERSON', 'TAYLOR', 'THOMAS', 'HERNANDEZ', 'MOORE', 'MARTIN', 'JACKSON', 'THOMPSON', 'WHITE', 'LOPEZ', 'LEE', 'GONZALEZ', 'HARRIS', 'CLARK', 'LEWIS', 'ROBINSON', 'WALKER', 'PEREZ', 'HALL', 'YOUNG', 'ALLEN', 'SANCHEZ', 'WRIGHT', 'KING', 'SCOTT', 'GREEN', 'BAKER', 'ADAMS', 'NELSON', 'HILL', 'RAMIREZ', 'CAMPBELL', 'MITCHELL', 'ROBERTS', 'CARTER', 'PHILLIPS', 'EVANS', 'TURNER', 'TORRES', 'PARKER', 'COLLINS', 'EDWARDS', 'STEWART', 'FLORES', 'MORRIS', 'NGUYEN', 'MURPHY', 'RIVERA', 'COOK', 'ROGERS', 'MORGAN', 'PETERSON', 'COOPER', 'REED', 'BAILEY', 'BELL', 'GOMEZ', 'KELLY', 'HOWARD', 'WARD']

DOMAINS = ['eexxaammppllee.com', 'thatsalloneword.gov', 'circlecircledotdot.me', 'geemayul.tv', 'hawtmayul.org', 'flounderflipperflooder.mob', 'ihavetwocents.org', 'rubyourhandstogetherrealhard.com', 'clapyourhandsandsaynay.org', 'iliketrafficlights.gov', 'harumphguffaw.tv', 'ererlkejre.com', 'wwwwllllsssccc.gov', 'eeeeejjjjjaaaammmm.edu', 'ererwewesdsd.tv', 'bobobob.ch']

COMPANY_NAMES = ['big', 'silver', 'global', 'fantastic', 'somewhat', 'gravy', 'blink', 'light', 'dingo', 'transatlantic', 'super', 'infinite', 'infinity', 'hound', 'edge']
COMPANY_SUFFIXES = ['corp', 'llc', 'inc', 'gmb', 'universal', 'limited', 'partnership', 'co']


class Command(NoArgsCommand):
    help = "Destructively changes the database to remove identifying information.  Used when creating test fixtures."

    requires_model_validation = True

    def generate_phone_number(self): return '206-%s-%s' % (''.join([str(random.randint(0, 9)) for x in range(3)]), ''.join([str(random.randint(0, 9)) for x in range(4)]))

    def generate_email(self, member):
        from nadine.models import Member
        email = self.cons_email(member)
        while Member.objects.filter(user__email=email).count() > 0:
            email = self.cons_email(member)
        return email

    def generate_name(self, is_male):
        from nadine.models import Member
        first_name, last_name = self._cons_name(is_male)
        while Member.objects.filter(user__first_name=first_name, user__last_name=last_name).count() > 0:
            first_name, last_name = self._cons_name(is_male)
        return (first_name, last_name)

    def _cons_name(self, is_male):
        if is_male:
            return (self.capitalize_name(MALE_FIRST_NAMES[random.randint(0, len(MALE_FIRST_NAMES) - 1)]), self.capitalize_name(LAST_NAMES[random.randint(0, len(LAST_NAMES) - 1)]))
        return (self.capitalize_name(FEMALE_FIRST_NAMES[random.randint(0, len(FEMALE_FIRST_NAMES) - 1)]), self.capitalize_name(LAST_NAMES[random.randint(0, len(LAST_NAMES) - 1)]))

    def cons_email(self, member): return '%s_%s@%s' % (member.first_name.lower(), member.last_name.lower(), DOMAINS[random.randint(0, len(DOMAINS) - 1)])

    def generate_company(self): return '%s %s %s' % (self.capitalize_name(COMPANY_NAMES[random.randint(0, len(COMPANY_NAMES) - 1)]), self.capitalize_name(COMPANY_NAMES[random.randint(0, len(COMPANY_NAMES) - 1)]), self.capitalize_name(COMPANY_SUFFIXES[random.randint(0, len(COMPANY_SUFFIXES) - 1)]))

    def capitalize_name(self, name): return '%s%s' % (name[0].upper(), ''.join([c.lower() for c in name[1:]]))

    def handle_noargs(self, **options):
        from nadine.models import Member, Transaction, DailyLog, Membership
        from django.core.files import File
        pseudonymous_image = open('media/BlankIcon150x150.jpg', 'r')

        for log in Membership.objects.all():
            if log.note != None and len(log.note) > 0:
                log.note = 'Some admin note here.'
                log.save()

        for log in DailyLog.objects.all():
            if log.note != None and len(log.note) > 0:
                log.note = 'Some admin note here.'
                log.save()

        for transaction in Transaction.objects.all():
            if transaction.note != None and len(transaction.note) > 0:
                transaction.note = 'Some admin note here.'
                transaction.save()

        # Force all users to have Member records
        for user in User.objects.all():
            user.save()

        for member in Member.objects.all():
            member.user.first_name, member.user.last_name = self.generate_name(member.gender == 'M')
            member.user.username = '%s_%s' % (member.user.first_name, member.user.last_name)
            member.user.set_password('1234')  # User.objects.make_random_password()
            member.user.email = self.generate_email(member)
            member.email2 = None
            member.phone = self.generate_phone_number()
            member.phone2 = ''
            member.url_personal = 'http://%s/' % DOMAINS[random.randint(0, len(DOMAINS) - 1)]
            member.company_name = self.generate_company()
            if member.photo:
                member.photo.save("PseudoPhoto.jpg", File(pseudonymous_image), save=False)
            member.user.save()
            member.save()

        # Set up a known account so that we can log in for demos
        if User.objects.filter(is_staff=True).count() > 0:
            admin = User.objects.filter(is_staff=True)[0]
            admin.username = 'Staff_Member'
            admin.first_name = 'Staff'
            admin.last_name = 'Member'
            admin.set_password('1234')
            admin.save()

# Copyright 2010 Office Nomads LLC (http://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
